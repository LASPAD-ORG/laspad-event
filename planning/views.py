import secrets
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages

from .models import AuthorizedMember, LoginToken, LabEvent
from .forms import LabEventForm


# ────────────────────────────────────────────────
#  Authentification "lien magique" (par e-mail)
# ────────────────────────────────────────────────
def _current_member(request):
    email = request.session.get('planning_email')
    if not email:
        return None
    return AuthorizedMember.objects.filter(email__iexact=email, is_active=True).first()


def planning_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if _current_member(request) is None:
            return redirect('planning:login')
        return view(request, *args, **kwargs)
    return wrapper


def login_view(request):
    """Le membre saisit son e-mail ; s'il est autorisé, on lui envoie un lien de connexion."""
    if _current_member(request):
        return redirect('planning:agenda')

    ctx = {'sent': False, 'error': None, 'email': ''}
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        ctx['email'] = email
        member = AuthorizedMember.objects.filter(email__iexact=email, is_active=True).first()
        if not member:
            # message volontairement neutre (ne pas révéler qui est autorisé)
            ctx['error'] = "Cet e-mail n'est pas autorisé. Contactez l'administration du LASPAD si besoin."
            return render(request, 'planning/login.html', ctx)

        token = LoginToken.objects.create(token=secrets.token_urlsafe(32), email=member.email)
        link = request.build_absolute_uri(reverse('planning:auth', args=[token.token]))
        html = render_to_string('planning/email_login.html', {'link': link, 'name': member.name})
        msg = EmailMultiAlternatives(
            subject="Votre lien de connexion — Planning LASPAD",
            body=f"Bonjour,\n\nVoici votre lien de connexion au planning du labo :\n{link}\n\nCe lien est valable 45 minutes.",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[member.email],
        )
        msg.attach_alternative(html, "text/html")
        try:
            msg.send(fail_silently=False)
        except Exception:
            ctx['error'] = "Impossible d'envoyer l'e-mail pour le moment. Réessayez dans un instant."
            return render(request, 'planning/login.html', ctx)
        ctx['sent'] = True
    return render(request, 'planning/login.html', ctx)


def auth_view(request, token):
    """Le membre clique sur le lien reçu : on valide le jeton et on ouvre la session."""
    lt = LoginToken.objects.filter(token=token).first()
    if not lt or not lt.is_valid():
        return render(request, 'planning/login.html', {
            'sent': False, 'email': '',
            'error': "Ce lien de connexion est invalide ou expiré. Redemandez-en un ci-dessous.",
        })
    lt.used_at = timezone.now()
    lt.save(update_fields=['used_at'])
    request.session['planning_email'] = lt.email
    request.session.set_expiry(60 * 60 * 24 * 14)  # session 14 jours
    return redirect('planning:agenda')


def logout_view(request):
    request.session.pop('planning_email', None)
    return redirect('planning:login')


# ────────────────────────────────────────────────
#  Agenda + ajout
# ────────────────────────────────────────────────
@planning_required
def agenda_view(request):
    qs = LabEvent.objects.all()

    # Filtres
    f_statut = request.GET.get('statut', '')
    f_projet = request.GET.get('projet', '')
    f_resp   = request.GET.get('responsable', '')
    f_when   = request.GET.get('when', '')  # a_venir | passes | tous

    today = timezone.localdate()

    # Par défaut : « À venir ». Mais si rien n'est à venir et qu'il existe des
    # événements passés, on bascule automatiquement sur « Passés » pour ne jamais
    # afficher un écran vide (utile tant que l'agenda est surtout historique).
    auto_passes = False
    if not f_when:
        f_when = 'a_venir'
        has_upcoming = LabEvent.objects.filter(date_debut__gte=today).exists()
        if not has_upcoming and LabEvent.objects.exists():
            f_when = 'passes'
            auto_passes = True

    if f_when == 'a_venir':
        qs = qs.filter(date_debut__gte=today)
    elif f_when == 'passes':
        qs = qs.filter(date_debut__lt=today).order_by('-date_debut', 'heure')
    if f_statut:
        qs = qs.filter(statut=f_statut)
    if f_projet:
        qs = qs.filter(projet=f_projet)
    if f_resp:
        qs = qs.filter(responsable=f_resp)

    # Groupement par date
    groups = []
    current = None
    for ev in qs:
        if current is None or current['date'] != ev.date_debut:
            current = {'date': ev.date_debut, 'events': []}
            groups.append(current)
        current['events'].append(ev)

    all_events = LabEvent.objects.all()
    context = {
        'groups':      groups,
        'count':       qs.count(),
        'member':      _current_member(request),
        'statuts':     LabEvent.STATUT_CHOICES,
        'projets':     sorted({e.projet for e in all_events if e.projet}),
        'responsables': sorted({e.responsable for e in all_events if e.responsable}),
        'f_statut': f_statut, 'f_projet': f_projet, 'f_resp': f_resp, 'f_when': f_when,
        'auto_passes': auto_passes,
        'today': today,
        'total_all':   all_events.count(),
        'total_avenir': all_events.filter(date_debut__gte=today).count(),
    }
    return render(request, 'planning/agenda.html', context)


@planning_required
def add_view(request):
    member = _current_member(request)
    if request.method == 'POST':
        form = LabEventForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.created_by = member.email
            ev.save()
            messages.success(request, "Événement ajouté au planning ✅")
            return redirect('planning:agenda')
    else:
        form = LabEventForm()

    all_events = LabEvent.objects.all()
    return render(request, 'planning/add.html', {
        'form': form,
        'member': member,
        'projets':      sorted({e.projet for e in all_events if e.projet}),
        'responsables': sorted({e.responsable for e in all_events if e.responsable}),
        'lieux':        sorted({e.lieu for e in all_events if e.lieu}),
        'types':        sorted({e.type_event for e in all_events if e.type_event}),
    })


@planning_required
def edit_view(request, pk):
    member = _current_member(request)
    ev = get_object_or_404(LabEvent, pk=pk)
    if request.method == 'POST':
        form = LabEventForm(request.POST, instance=ev)
        if form.is_valid():
            form.save()
            messages.success(request, "Événement mis à jour ✅")
            return redirect('planning:agenda')
    else:
        form = LabEventForm(instance=ev)

    all_events = LabEvent.objects.all()
    return render(request, 'planning/add.html', {
        'form': form, 'member': member, 'editing': ev,
        'projets':      sorted({e.projet for e in all_events if e.projet}),
        'responsables': sorted({e.responsable for e in all_events if e.responsable}),
        'lieux':        sorted({e.lieu for e in all_events if e.lieu}),
        'types':        sorted({e.type_event for e in all_events if e.type_event}),
    })
