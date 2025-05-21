from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from .models import Client, Compte, Transaction
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User

# ============================ AUTH ============================


def login_view(request):
    if request.method == 'POST':
        identifiant = request.POST.get('identifiant').strip()
        mot_de_passe = request.POST.get('mot_de_passe').strip()

        if not identifiant:
            messages.error(request, "Merci de renseigner votre identifiant!")
            return render(request, 'login.html')

        try:
            client = Client.objects.get(identifiant=identifiant)
            if mot_de_passe == client.password:
                request.session['client_id'] = client.id
                return redirect('home')
            else:
                messages.error(request, "Mot de passe incorrect.")
        except Client.DoesNotExist:
            messages.error(request, "Client introuvable.")

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

#from django.contrib.auth.models import User

def register_view(request):
    if request.method == 'POST':
        identifiant = request.POST.get('identifiant')
        mot_de_passe = request.POST.get('mot_de_passe')
        confirmer_mot_de_passe = request.POST.get('confirmer_mot_de_passe')
        cin = request.POST.get('cin')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        adresse = request.POST.get('adresse')
        tel = request.POST.get('tel')

        # Vérification des champs vides
        if not all([identifiant, cin, nom, prenom, adresse, tel, mot_de_passe, confirmer_mot_de_passe]):
            messages.error(request, "Tous les champs sont obligatoires.")
            return render(request, 'register.html')

        # Vérification des mots de passe
        if mot_de_passe != confirmer_mot_de_passe:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'register.html')

        # Vérification de l'identifiant déjà existant
        if Client.objects.filter(identifiant=identifiant).exists():
            messages.error(request, f"L'identifiant '{identifiant}' est déjà utilisé. Choisissez-en un autre.")
            return render(request, 'register.html')

        # Vérification du CIN
        if Client.objects.filter(cin=cin).exists():
            messages.error(request, f"Le CIN '{cin}' est déjà enregistré.")
            return render(request, 'register.html')

        # Création du User Django
        user = User.objects.create_user(username=str(identifiant), password=mot_de_passe)

        # Création du Client lié au User
        client = Client.objects.create(
            user=user,
            identifiant=identifiant,
            cin=cin,
            nom=nom,
            prenom=prenom,
            adresse=adresse,
            tel=tel,
            password=mot_de_passe  # Attention ici, si tu as déjà user.password, ce champ dans Client est redondant
        )

        # Création du compte associé
        Compte.objects.create(
            numero=f"COMPT-{client.id}",
            type="Standard",
            client=client,
            solde=0.0
        )

        request.session['client_id'] = client.id
        messages.success(request, "Compte créé avec succès !")
        return redirect('home')

    return render(request, 'register.html')


# ============================ HOME ============================

def home(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')

    try:
        client = Client.objects.get(id=client_id)
        comptes = client.comptes.all()
        transactions = Transaction.objects.filter(compte__in=comptes).order_by('-date')
    except Client.DoesNotExist:
        return redirect('login')

    return render(request, 'home.html', {
        'client': client,
        'comptes': comptes,
        'transactions': transactions
    })

# ============================ FONCTIONS ============================

@require_POST
def creer_compte_epargne(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')

    client = Client.objects.get(id=client_id)

    # Vérifier s'il a déjà un compte épargne
    if client.comptes.filter(type="Épargne").exists():
        messages.info(request, "Vous avez déjà un compte épargne.")
        return redirect('home')

    # Générer un numéro sous la forme compt-epargne-<num>
    def generer_numero_unique():
        dernier_id = 1
        while True:
            numero = f"COMPT-EPARGNE-{dernier_id}"
            if not Compte.objects.filter(numero=numero).exists():
                return numero
            dernier_id += 1

    numero_unique = generer_numero_unique()

    # Création du compte
    Compte.objects.create(
        numero=numero_unique,
        type="Épargne",
        client=client,
        solde=0.0
    )

    messages.success(request, f"Compte épargne créé avec succès.")
    return redirect('home')



def versement(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')

    if request.method == 'POST':
        compte_id = request.POST.get('compte_id')
        montant = request.POST.get('montant')

        if not compte_id or not montant:
            messages.error(request, "Tous les champs doivent être remplis.")
            return redirect('versement')

        try:
            montant = Decimal(montant)
            if montant <= 0:
                raise ValueError("Montant non valide.")
        except (ValueError, InvalidOperation):
            messages.error(request, "Le montant doit être un nombre valide et supérieur à zéro.")
            return redirect('versement')

        try:
            compte = Compte.objects.get(id=compte_id, client__id=client_id)
        except Compte.DoesNotExist:
            messages.error(request, "Le compte spécifié n'existe pas.")
            return redirect('versement')

        compte.solde += montant
        compte.save()

        Transaction.objects.create(
            libelle="Versement",
            montant=montant,
            compte=compte,
            date=timezone.now()
        )

        messages.success(request, "Versement effectué avec succès.")
        return redirect('home')  # Reste sur la page de versement

    # Si GET, afficher le formulaire
    comptes = Compte.objects.filter(client__id=client_id)
    return render(request, 'versement.html', {'comptes': comptes})


@require_http_methods(["GET", "POST"])
def retrait(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')

    if request.method == "POST":
        compte_id = request.POST.get('compte_id')
        montant = request.POST.get('montant')

        try:
            montant = Decimal(montant)
            compte = Compte.objects.get(id=compte_id, client__id=client_id)

            if montant <= 0:
                raise ValueError("Montant invalide.")
            if compte.solde < montant:
                messages.error(request, "Solde insuffisant pour effectuer le retrait.")
                return redirect('retrait')

            compte.solde -= montant
            compte.save()

            Transaction.objects.create(libelle="Retrait", montant=-montant, compte=compte)
            messages.success(request, "Retrait effectué avec succès.")
        except (Compte.DoesNotExist, ValueError, InvalidOperation):
            messages.error(request, "Erreur lors du retrait.")

        return redirect('home')

    # GET : afficher la page avec la liste des comptes
    comptes = Compte.objects.filter(client__id=client_id)
    return render(request, 'retrait.html', {'comptes': comptes})


def virement(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')

    comptes = Compte.objects.filter(client__id=client_id)

    if request.method == 'POST':
        source_compte_id = request.POST.get('source_compte')
        destination_compte_numero = request.POST.get('destination_compte')
        montant = request.POST.get('montant')

        if not source_compte_id or not destination_compte_numero or not montant:
            messages.error(request, "Tous les champs doivent être remplis.")
            return render(request, 'virement.html', {'comptes': comptes})

        try:
            montant = Decimal(montant)
        except:
            messages.error(request, "Le montant doit être un nombre valide.")
            return render(request, 'virement.html', {'comptes': comptes})

        if montant <= 0:
            messages.error(request, "Le montant doit être supérieur à zéro.")
            return render(request, 'virement.html', {'comptes': comptes})

        # Récupérer les objets des comptes source et destination
        source_compte = get_object_or_404(Compte, id=source_compte_id)
        destination_compte = get_object_or_404(Compte, numero=destination_compte_numero)

        if source_compte.solde < montant:
            messages.error(request, "Solde insuffisant pour effectuer le virement.")
            return render(request, 'virement.html', {'comptes': comptes})

        # Vérification spéciale pour un compte épargne
        if source_compte.type.strip().lower() == 'épargne':
            # Chercher un compte standard associé au même client
            compte_standard = Compte.objects.filter(
                client_id=client_id,
                type__iexact='standard'
            ).first()

            # Si aucun compte standard trouvé, afficher une erreur
            if not compte_standard:
                messages.error(request, "Aucun compte standard correspondant à votre compte épargne n'a été trouvé.")
                return render(request, 'virement.html', {'comptes': comptes})

            # Vérifier si le virement est effectué vers le compte standard
            if destination_compte.id != compte_standard.id:
                messages.error(request, "Depuis un compte épargne, vous ne pouvez effectuer un virement que vers votre propre compte standard.")
                return render(request, 'virement.html', {'comptes': comptes})

        # Exécution du virement
        source_compte.solde -= montant
        destination_compte.solde += montant
        source_compte.save()
        destination_compte.save()

        # Enregistrer les transactions
        Transaction.objects.create(
            compte=source_compte,
            date=timezone.now(),
            libelle=f'Virement vers {destination_compte.numero}',
            montant=-montant
        )

        Transaction.objects.create(
            compte=destination_compte,
            date=timezone.now(),
            libelle=f'Virement reçu de {source_compte.numero}',
            montant=montant
        )

        messages.success(request, "Virement effectué avec succès.")
        return render(request, 'home.html', {'comptes': comptes})

    return render(request, 'virement.html', {'comptes': comptes})


def historique(request):
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')

    try:
        client = Client.objects.get(id=client_id)
        comptes = client.comptes.all()

        # Transactions compte standard
        comptes_standard = comptes.filter(type='standard')
        transactions_standard = Transaction.objects.filter(compte__in=comptes_standard).order_by('-date')

        # Transactions compte épargne
        comptes_epargne = comptes.filter(type='epargne')
        transactions_epargne = Transaction.objects.filter(compte__in=comptes_epargne).order_by('-date')

    except Client.DoesNotExist:
        return redirect('login')

    context = {
        'transactions_standard': transactions_standard,
        'transactions_epargne': transactions_epargne,
    }
    return render(request, 'historique.html', context)




# forms.py
from django import forms
from .models import Client

class ProfilForm(forms.ModelForm):
    nouveau_mot_de_passe = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Nouveau mot de passe"
    )
    confirmer_mot_de_passe = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmer le mot de passe"
    )

    class Meta:
        model = Client
        fields = ['identifiant', 'cin', 'nom', 'prenom', 'adresse', 'tel']
        widgets = {
            'identifiant': forms.TextInput(attrs={'class': 'form-control'}),
            'cin': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'tel': forms.TextInput(attrs={'class': 'form-control'}),
        }

from django.contrib.auth.decorators import login_required
@login_required
def profil(request):
    client = get_object_or_404(Client, user=request.user)
    user = request.user

    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=client)
        if form.is_valid():
            # Modification des infos personnelles
            form.save()

            # Gestion du mot de passe
            nouveau_mdp = form.cleaned_data.get('nouveau_mot_de_passe')
            confirmer_mdp = form.cleaned_data.get('confirmer_mot_de_passe')

            if nouveau_mdp or confirmer_mdp:
                if nouveau_mdp != confirmer_mdp:
                    messages.error(request, "Les mots de passe ne correspondent pas.")
                    return render(request, 'profil.html', {'form': form, 'client': client})
                else:
                    user.set_password(nouveau_mdp)
                    user.save()
                    messages.success(request, "Mot de passe modifié avec succès. Veuillez vous reconnecter.")
                    return redirect('login')  # Redirection vers la page de connexion

            messages.success(request, "Informations mises à jour avec succès.")
            return redirect('profil')
        else:
            messages.error(request, "Erreur lors de la mise à jour.")
    else:
        form = ProfilForm(instance=client)

    return render(request, 'profil.html', {'form': form, 'client': client})


def contact(request):
    message_envoye = False

    if request.method == 'POST':
        # Ici tu pourrais récupérer les données si tu veux les traiter :
        # nom = request.POST.get('name')
        # email = request.POST.get('email')
        # message = request.POST.get('message')
        message_envoye = True

    return render(request, 'contact.html', {'message_envoye': message_envoye})