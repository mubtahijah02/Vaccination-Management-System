from django.test import TestCase
from django.urls import reverse

from .models import Child, CustomUser, Hospital, Parent, VaccinationRecord


class ParentDashboardTests(TestCase):
	def setUp(self):
		self.parent_user = CustomUser.objects.create_user(
			username='parent-one',
			email='parent@example.test',
			password='VaxCare-test-2026!',
			role='parent',
		)
		self.parent = Parent.objects.create(user=self.parent_user)
		self.other_parent_user = CustomUser.objects.create_user(
			username='parent-two',
			password='VaxCare-test-2026!',
			role='parent',
		)
		self.other_parent = Parent.objects.create(user=self.other_parent_user)

	def test_dashboard_requires_parent_login(self):
		response = self.client.get(reverse('parent_dashboard'))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(
			response.url,
			f"{reverse('login')}?next={reverse('parent_dashboard')}",
		)

	def test_dashboard_only_shows_signed_in_parents_records(self):
		Child.objects.create(parent=self.parent, name='Own child', date_of_birth='2020-01-02')
		Child.objects.create(parent=self.other_parent, name='Other child', date_of_birth='2021-03-04')
		self.parent.phone = '555-0100'
		self.parent.save()
		self.client.force_login(self.parent_user)

		response = self.client.get(reverse('parent_dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'parent-one')
		self.assertContains(response, 'parent@example.test')
		self.assertContains(response, '555-0100')
		self.assertContains(response, 'Own child')
		self.assertNotContains(response, 'Other child')

	def test_parent_can_update_contact_details(self):
		self.client.force_login(self.parent_user)

		response = self.client.post(reverse('parent_profile_update'), {
			'phone': '555-0199',
			'address': '10 Family Road',
		})

		self.assertRedirects(response, reverse('parent_dashboard'))
		self.parent.refresh_from_db()
		self.assertEqual(self.parent.phone, '555-0199')
		self.assertEqual(self.parent.address, '10 Family Road')

	def test_parent_can_add_child_schedule_and_complete_vaccination(self):
		self.client.force_login(self.parent_user)

		response = self.client.post(reverse('child_add'), {
			'name': 'Sam',
			'date_of_birth': '2020-05-12',
		})

		self.assertRedirects(response, reverse('parent_dashboard'))
		child = Child.objects.get(parent=self.parent, name='Sam')
		response = self.client.post(reverse('vaccination_add', args=[child.id]), {
			'vaccine_name': 'Example vaccine',
			'dose_number': 1,
			'scheduled_date': '2026-11-10',
		})
		self.assertRedirects(response, reverse('parent_dashboard'))
		record = VaccinationRecord.objects.get(child=child)
		self.assertEqual(record.status, VaccinationRecord.SCHEDULED)

		response = self.client.post(
			reverse('vaccination_mark_completed', args=[record.id]),
			{'administered_date': '2026-10-01'},
		)

		self.assertRedirects(response, reverse('parent_dashboard'))
		record.refresh_from_db()
		self.assertEqual(record.status, VaccinationRecord.COMPLETED)
		self.assertEqual(str(record.administered_date), '2026-10-01')
		self.assertContains(self.client.get(reverse('parent_dashboard')), 'Recorded administered')

	def test_parent_cannot_access_another_parents_child(self):
		child = Child.objects.create(
			parent=self.other_parent,
			name='Private child',
			date_of_birth='2021-03-04',
		)
		self.client.force_login(self.parent_user)

		response = self.client.get(reverse('vaccination_add', args=[child.id]))

		self.assertEqual(response.status_code, 404)

	def test_non_parent_cannot_open_parent_dashboard(self):
		hospital_user = CustomUser.objects.create_user(
			username='hospital-one',
			password='VaxCare-test-2026!',
			role='hospital',
		)
		Hospital.objects.create(user=hospital_user)
		self.client.force_login(hospital_user)

		response = self.client.get(reverse('parent_dashboard'))

		self.assertEqual(response.status_code, 403)
