from django import forms
from .models import LabEvent


class LabEventForm(forms.ModelForm):
    class Meta:
        model = LabEvent
        fields = [
            'projet', 'type_event', 'titre', 'description',
            'date_debut', 'heure', 'date_fin',
            'responsable', 'invites',
            'besoins_com', 'besoins_prod',
            'lieu', 'statut', 'budget',
        ]
        widgets = {
            'projet':       forms.TextInput(attrs={'class': 'f-input', 'list': 'projets', 'placeholder': 'Ex. Séminaire, Cours Medits, Multilatéralisme…'}),
            'titre':        forms.TextInput(attrs={'class': 'f-input', 'placeholder': "Titre de l'événement"}),
            'description':  forms.Textarea(attrs={'class': 'f-input', 'rows': 2, 'placeholder': 'Courte description (optionnel)'}),
            'date_debut':   forms.DateInput(attrs={'class': 'f-input', 'type': 'date'}),
            'heure':        forms.TimeInput(attrs={'class': 'f-input', 'type': 'time'}),
            'date_fin':     forms.DateInput(attrs={'class': 'f-input', 'type': 'date'}),
            'responsable':  forms.TextInput(attrs={'class': 'f-input', 'list': 'responsables', 'placeholder': 'Qui pilote ?'}),
            'invites':      forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'Invité(s) éventuel(s)'}),
            'besoins_com':  forms.Textarea(attrs={'class': 'f-input', 'rows': 2, 'placeholder': 'Affiche, réseaux, Mailchimp, lien Zoom…'}),
            'besoins_prod': forms.Textarea(attrs={'class': 'f-input', 'rows': 2, 'placeholder': 'Tournage, enregistrement, post-production…'}),
            'lieu':         forms.TextInput(attrs={'class': 'f-input', 'list': 'lieux', 'placeholder': 'En ligne, Sur place (bureau direction)…'}),
            'statut':       forms.Select(attrs={'class': 'f-input'}),
            'budget':       forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'Ex. 100 000 (optionnel)'}),
        }

    # Type libre (avec suggestions) plutôt qu'une liste figée : les données réelles
    # contiennent des types variés ("Reunion", "Table ronde", "UPANZI"…).
    type_event = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'f-input', 'list': 'types',
            'placeholder': 'Ex. Formation, Séminaire, Réunion…',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # champs obligatoires minimaux : titre + date de début
        for name, field in self.fields.items():
            field.required = name in ('titre', 'date_debut', 'type_event', 'statut')
