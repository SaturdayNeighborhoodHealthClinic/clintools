import datetime

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.timezone import now
from rest_framework.test import APITestCase

from pttrack import models
from workup import models as workupModels
from pttrack.test_views import build_provider, log_in_provider

BASIC_FIXTURE = 'api.json'

class APITest(APITestCase):
    fixtures = [BASIC_FIXTURE]

    def setUp(self):
        workupModels.ClinicType.objects.create(name="Basic Care Clinic")
        workupModels.ClinicDate.objects.create(
            clinic_type=workupModels.ClinicType.objects.all()[0],
            clinic_date=now().date()+datetime.timedelta(days=1),
            gcal_id="tmp")
        workupModels.ClinicDate.objects.create(
            clinic_type=workupModels.ClinicType.objects.all()[0],
            clinic_date=now().date()-datetime.timedelta(days=1),
            gcal_id="tmp")
        log_in_provider(self.client, build_provider(["Coordinator"]))

    def test_api_correctly_lists_patients(self):
        pt1 = models.Patient.objects.get(pk=1)

        pt2 = models.Patient.objects.create(
            first_name="Juggie",
            last_name="Brodeltein",
            middle_name="Bayer",
            phone='+49 178 236 5288',
            gender=models.Gender.objects.all()[1],
            address='Schulstrasse 9',
            city='Munich',
            state='BA',
            zip_code='63108',
            pcp_preferred_zip='63018',
            date_of_birth=datetime.date(1990, 01, 01),
            patient_comfortable_with_english=False,
            preferred_contact_method=models.ContactMethod.objects.all()[0],
        )

        pt3 = models.Patient.objects.create(
            first_name="Asdf",
            last_name="Lkjh",
            middle_name="Bayer",
            phone='+49 178 236 5288',
            gender=models.Gender.objects.all()[0],
            address='Schulstrasse 9',
            city='Munich',
            state='BA',
            zip_code='63108',
            pcp_preferred_zip='63018',
            date_of_birth=datetime.date(1990, 01, 01),
            patient_comfortable_with_english=False,
            preferred_contact_method=models.ContactMethod.objects.all()[0],
        )

        pt4 = models.Patient.objects.create(
            first_name="No",
            last_name="Action",
            middle_name="Item",
            phone='+12 345 678 9000',
            gender=models.Gender.objects.all()[0],
            address='Schulstrasse 9',
            city='Munich',
            state='BA',
            zip_code='63108',
            pcp_preferred_zip='63018',
            date_of_birth=datetime.date(1990, 01, 01),
            patient_comfortable_with_english=False,
            preferred_contact_method=models.ContactMethod.objects.all()[0],
        )

        # Give pt2 a workup one day later.
        workupModels.Workup.objects.create(
                clinic_day=workupModels.ClinicDate.objects.all()[0], # one day later
                chief_complaint="SOB",
                diagnosis="MI",
                HPI="", PMH_PSH="", meds="", allergies="", fam_hx="", soc_hx="",
                ros="", pe="", A_and_P="",
                author=models.Provider.objects.all()[0],
                author_type=models.ProviderType.objects.all()[0],
                patient=pt2)

        # Give pt3 a workup one days before.
        workupModels.Workup.objects.create(
                clinic_day=workupModels.ClinicDate.objects.all()[1], # one day before
                chief_complaint="SOB",
                diagnosis="MI",
                HPI="", PMH_PSH="", meds="", allergies="", fam_hx="", soc_hx="",
                ros="", pe="", A_and_P="",
                author=models.Provider.objects.all()[0],
                author_type=models.ProviderType.objects.all()[0],
                patient=pt3)

        # make pt1 have and AI due tomorrow
        pt1_ai = models.ActionItem.objects.create(
            author=models.Provider.objects.all()[0],
            author_type=models.ProviderType.objects.all()[0],
            instruction=models.ActionInstruction.objects.all()[0],
            due_date=now().date()+datetime.timedelta(days=1),
            comments="",
            patient=pt1)

        # make pt2 have an AI due yesterday
        pt2_ai = models.ActionItem.objects.create(
            author=models.Provider.objects.all()[0],
            author_type=models.ProviderType.objects.all()[0],
            instruction=models.ActionInstruction.objects.all()[0],
            due_date=now().date()-datetime.timedelta(days=1),
            comments="",
            patient=pt2)

        # make pt3 have an AI that during the test will be marked done
        pt3_ai = models.ActionItem.objects.create(
            author=models.Provider.objects.all()[0],
            author_type=models.ProviderType.objects.all()[0],
            instruction=models.ActionInstruction.objects.all()[0],
            due_date=now().date()-datetime.timedelta(days=15),
            comments="",
            patient=pt3)

        url = reverse("pt_list_api")

        # Test last_name ordering
        data = {'sort':'last_name'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.data[0]['last_name'],response.data[1]['last_name'])
        self.assertLessEqual(response.data[1]['last_name'],response.data[2]['last_name'])
        self.assertLessEqual(response.data[2]['last_name'],response.data[3]['last_name'])

        # Test workup/intake ordering.
        data = {'sort':'latest_workup'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data[0]['latest_workup'], None) # pt2, workup date now()+1day
        self.assertEqual(response.data[1]['latest_workup'], None) # pt4, intake date now
        self.assertNotEqual(response.data[2]['latest_workup'], None) # pt3, workup date now()-1day
        self.assertEqual(response.data[3]['latest_workup'], None) # pt1, intake date 2016-01-02

        # Check that dates are correcly sorted
        self.assertGreaterEqual(response.data[0]['latest_workup']['clinic_day']['clinic_date'],response.data[1]['history']['last']['history_date'])
        self.assertGreaterEqual(response.data[1]['history']['last']['history_date'],response.data[2]['latest_workup']['clinic_day']['clinic_date'])
        self.assertGreaterEqual(response.data[2]['latest_workup']['clinic_day']['clinic_date'],response.data[3]['history']['last']['history_date'])
        
        # Test for unsigned_workup
        data = {'filter':'unsigned_workup'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2) # check that all of the two patients with workups are returned
        self.assertNotEqual(response.data[0]['latest_workup'], None)
        self.assertNotEqual(response.data[1]['latest_workup'], None)
        self.assertLessEqual(response.data[0]['last_name'],response.data[1]['last_name']) # check that sorting is correct

        # Test displaying active patients (needs_workup is true).
        data = {'filter':'active'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0) # default needs_workup is false

        pt1.change_active_status()
        pt1.save()
        pt2.change_active_status()
        pt2.save()
        
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['needs_workup'], True)
        self.assertEqual(response.data[1]['needs_workup'], True)
        self.assertLessEqual(response.data[0]['last_name'],response.data[1]['last_name']) # check that sorting is correct

        # Test displaying patients with active action items (active means not due in the future?)
        data = {'filter':'ai_active'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2) #pt2, pt3 should be present since pt 1 is not past due and pt4 has no ai   

        # Test displaying patients with inactive action items
        data = {'filter':'ai_inactive'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], pt1.id)

        pt3_ai.mark_done(models.Provider.objects.all()[0])
        pt3_ai.save()

        # Test now only has pt2
        data = {'filter':'ai_active'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200) # Not sure if I should keep repeating this line
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], pt2.id)

        # Should be unchanged, still only have pt1
        data = {'filter':'ai_inactive'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], pt1.id)