from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    identifiant = models.IntegerField(unique=True,null=True, blank=True)
    cin = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    adresse = models.TextField()
    tel = models.CharField(max_length=15)
    password = models.CharField(max_length=128)


    def __str__(self):
        return f"{self.nom} {self.prenom}"

class Compte(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=20)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="comptes")
    solde = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Compte {self.numero}"

class Transaction(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    libelle = models.CharField(max_length=100)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name="transactions")

    def __str__(self):
        return f"{self.libelle} - {self.montant}"

class AgentBancaire(models.Model):
    matricule = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    tel = models.CharField(max_length=15)
    adresse = models.CharField(max_length=255, default="Adresse par défaut")

    def __str__(self):
        return f"{self.nom} {self.prenom}"



