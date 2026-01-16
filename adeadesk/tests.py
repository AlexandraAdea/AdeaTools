from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.urls import reverse

from adeacore.models import Client


class ClientCRUDTestCase(TestCase):
    """Tests für Client CRUD-Operationen in AdeaDesk."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client_firma = Client.objects.create(
            name="Test Firma",
            client_type="FIRMA",
            city="Zürich",
            email="firma@test.ch",
            lohn_aktiv=True
        )
        self.client_privat = Client.objects.create(
            name="Test Privatperson",
            client_type="PRIVAT",
            city="Bern",
            email="privat@test.ch",
            lohn_aktiv=False
        )
        self.test_client = TestClient()
    
    def test_client_list_requires_login(self):
        """Test dass Client-Liste Login erfordert."""
        response = self.test_client.get(reverse('adeadesk:client-list'))
        self.assertEqual(response.status_code, 302)  # Redirect zu Login
        self.assertIn('/login/', response.url)
    
    def test_client_list_shows_all_clients(self):
        """Test dass Client-Liste alle Clients zeigt."""
        self.test_client.login(username='testuser', password='testpass123')
        response = self.test_client.get(reverse('adeadesk:client-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.client_firma.name)
        self.assertContains(response, self.client_privat.name)
    
    def test_client_list_filters_by_type(self):
        """Test dass Client-Liste nach Typ filtert."""
        self.test_client.login(username='testuser', password='testpass123')
        # Filter nach FIRMA
        response = self.test_client.get(reverse('adeadesk:client-list') + '?client_type=FIRMA')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.client_firma.name)
        self.assertNotContains(response, self.client_privat.name)
        
        # Filter nach PRIVAT
        response = self.test_client.get(reverse('adeadesk:client-list') + '?client_type=PRIVAT')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.client_privat.name)
        self.assertNotContains(response, self.client_firma.name)
    
    def test_client_list_search(self):
        """Test dass Suche funktioniert."""
        self.test_client.login(username='testuser', password='testpass123')
        # Suche funktioniert über Name (Klartext). Verschlüsselte Felder wie `city` sind
        # nicht sinnvoll per DB-Filter durchsuchbar.
        response = self.test_client.get(reverse('adeadesk:client-list') + '?q=Test Firma')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.client_firma.name)
        self.assertNotContains(response, self.client_privat.name)
    
    def test_client_create_requires_login(self):
        """Test dass Client-Erstellung Login erfordert."""
        response = self.test_client.get(reverse('adeadesk:client-create'))
        self.assertEqual(response.status_code, 302)
    
    def test_client_create_with_firma_type(self):
        """Test dass Client mit FIRMA-Typ erstellt werden kann."""
        self.test_client.login(username='testuser', password='testpass123')
        response = self.test_client.post(reverse('adeadesk:client-create'), {
            'name': 'Neue Firma',
            'client_type': 'FIRMA',
            'city': 'Basel',
            'email': 'neu@firma.ch',
            'mwst_pflichtig': 'on',
            'mwst_nr': 'CHE-123.456.789',
            'rechnungs_email': 'rechnung@firma.ch',
            'zahlungsziel_tage': '30',
            'kontaktperson_name': 'Max Mustermann',
            'lohn_aktiv': 'on',
        })
        self.assertEqual(response.status_code, 302)  # Redirect nach Detail
        client = Client.objects.get(name='Neue Firma', client_type='FIRMA')
        self.assertTrue(client.mwst_pflichtig)
        self.assertEqual(client.mwst_nr, 'CHE-123.456.789')
        self.assertEqual(client.rechnungs_email, 'rechnung@firma.ch')
        self.assertEqual(client.zahlungsziel_tage, 30)
        self.assertEqual(client.kontaktperson_name, 'Max Mustermann')
        self.assertTrue(client.lohn_aktiv)
    
    def test_client_create_with_privat_type(self):
        """Test dass Client mit PRIVAT-Typ erstellt werden kann."""
        self.test_client.login(username='testuser', password='testpass123')
        response = self.test_client.post(reverse('adeadesk:client-create'), {
            'name': 'Neue Privatperson',
            'client_type': 'PRIVAT',
            'city': 'Luzern',
            'email': 'neu@privat.ch',
            'geburtsdatum': '1980-01-15',
            'steuerkanton': 'ZH',
        })
        self.assertEqual(response.status_code, 302)
        client = Client.objects.get(name='Neue Privatperson', client_type='PRIVAT')
        self.assertEqual(str(client.geburtsdatum), '1980-01-15')
        self.assertEqual(client.steuerkanton, 'ZH')
    
    def test_client_detail_shows_client_type(self):
        """Test dass Detail-View client_type anzeigt."""
        self.test_client.login(username='testuser', password='testpass123')
        response = self.test_client.get(reverse('adeadesk:client-detail', args=[self.client_firma.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Firma')
        self.assertContains(response, self.client_firma.name)
    
    def test_client_update_requires_login(self):
        """Test dass Client-Update Login erfordert."""
        response = self.test_client.get(reverse('adeadesk:client-update', args=[self.client_firma.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_client_update(self):
        """Test dass Client aktualisiert werden kann."""
        self.test_client.login(username='testuser', password='testpass123')
        response = self.test_client.post(reverse('adeadesk:client-update', args=[self.client_firma.pk]), {
            'name': 'Geänderte Firma',
            'client_type': 'FIRMA',
            'city': 'Genf',
            'email': 'geaendert@firma.ch',
            'phone': '',
            'kontaktperson_name': '',
            'street': '',
            'house_number': '',
            'zipcode': '',
            'mwst_pflichtig': '',
            'mwst_nr': '',
            'rechnungs_email': '',
            'zahlungsziel_tage': '30',
            'uid': '',
            'interne_notizen': '',
        })
        self.assertEqual(response.status_code, 302)
        self.client_firma.refresh_from_db()
        self.assertEqual(self.client_firma.name, 'Geänderte Firma')
        self.assertEqual(self.client_firma.city, 'Genf')
    
    def test_client_delete_requires_login(self):
        """Test dass Client-Löschung Login erfordert."""
        response = self.test_client.get(reverse('adeadesk:client-delete', args=[self.client_firma.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_client_delete(self):
        """Test dass Client gelöscht werden kann."""
        self.test_client.login(username='testuser', password='testpass123')
        client_id = self.client_firma.pk
        response = self.test_client.post(reverse('adeadesk:client-delete', args=[client_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Client.objects.filter(pk=client_id).exists())
