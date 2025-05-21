# my_app/serializers.py
from rest_framework import serializers
from .models import Client, Compte, Transaction, AgentBancaire, Administrateur

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class CompteSerializer(serializers.ModelSerializer):
    client = ClientSerializer()
    class Meta:
        model = Compte
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    compte = CompteSerializer()
    class Meta:
        model = Transaction
        fields = '__all__'

class AgentBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentBancaire
        fields = '__all__'

class AdministrateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrateur
        fields = '__all__'
