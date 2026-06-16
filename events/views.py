from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Event
from registrations.models import Participant  # ← ajouter cette ligne


def event_list(request):
    events   = Event.objects.filter(status=Event.STATUS_PUBLISHED).select_related('location', 'organizer')
    now      = timezone.now()
    upcoming = events.filter(end_datetime__gte=now)   # pas encore terminé
    past     = events.filter(end_datetime__lt=now)    # terminé

    context = {
        'upcoming_events': upcoming,
        'past_events':     past,
    }
    return render(request, 'events/list.html', context)


def event_detail(request, slug):
    """Page détail d'un événement."""
    event = get_object_or_404(
        Event.objects.select_related('location', 'organizer')
                     .prefetch_related(
                         'speakers__user',
                         'days__sessions__speaker__user',
                     ),
        slug=slug,
        status=Event.STATUS_PUBLISHED,
    )

    # Chronogramme
    days = event.days.prefetch_related(
        'sessions__speaker__user'
    ).order_by('date', 'order')

    # Vérifier si inscription possible
    mode = getattr(event, 'participation_mode', 'online_only')
    if mode == 'onsite_only':
        can_register = not event.is_full_onsite and event.is_upcoming
    elif mode == 'online_only':
        can_register = not event.is_full_online and event.is_upcoming
    else:  # hybrid
        can_register = (not event.is_full_onsite or not event.is_full_online) and event.is_upcoming

    context = {
        'event':              event,
        'days':               days,
        'has_schedule':       days.exists(),
        'can_register':       can_register,
        'participation_mode': mode,
    }
    return render(request, 'events/detail.html', context)


def recordings_list(request):
    from django.core.paginator import Paginator
    events = Event.objects.filter(
        recording_url__isnull=False,
        status=Event.STATUS_PUBLISHED,
    ).exclude(recording_url='').order_by('-start_datetime')
    
    # Filtre par type
    event_type = request.GET.get('type', '')
    if event_type:
        events = events.filter(event_type=event_type)
    
    paginator = Paginator(events, 9)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'page_obj': page_obj,
        'event_types': Event.TYPE_CHOICES,
        'current_type': event_type,
    }
    return render(request, 'events/recordings.html', context)


def newsletter_unsubscribe(request, pk):
    """Vue publique — ne nécessite pas d'authentification."""
    participant = get_object_or_404(Participant, pk=pk)
    if participant.newsletter:
        participant.newsletter = False
        participant.save(update_fields=['newsletter'])
    return render(request, 'events/newsletter_unsubscribe.html', {
        'participant': participant,
        'already_done': not participant.newsletter,
    })