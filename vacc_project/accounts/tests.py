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
		self.parent_user.first_name = 'Amina'
		self.parent_user.last_name = 'Rahman'
		self.parent_user.save()
		Child.objects.create(parent=self.parent, name='Own child', date_of_birth='2020-01-02')
		Child.objects.create(parent=self.other_parent, name='Other child', date_of_birth='2021-03-04')
		self.parent.phone = '555-0100'
		self.parent.save()
		self.client.force_login(self.parent_user)

		response = self.client.get(reverse('parent_dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'parent-one')
		self.assertContains(response, 'Amina Rahman')
		self.assertContains(response, 'parent@example.test')
		self.assertContains(response, '555-0100')
		self.assertContains(response, 'Own child')
		self.assertNotContains(response, 'Other child')

	def test_parent_registration_saves_real_name(self):
		response = self.client.post(reverse('register_parent'), {
			'username': 'amina-rahman',
			'first_name': 'Amina',
			'last_name': 'Rahman',
			'email': 'amina@example.test',
			'password1': 'Amina-Clinic-Test-2026!',
			'password2': 'Amina-Clinic-Test-2026!',
		})

		self.assertRedirects(response, reverse('parent_dashboard'))
		user = CustomUser.objects.get(username='amina-rahman')
		self.assertEqual(user.get_full_name(), 'Amina Rahman')

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

	def test_parent_can_assign_vaccine_date_to_a_hospital(self):
		hospital_user = CustomUser.objects.create_user(
			username='assigned-clinic',
			password='VaxCare-test-2026!',
			role='hospital',
		)
		hospital = Hospital.objects.create(user=hospital_user, name='North Clinic')
		child = Child.objects.create(
			parent=self.parent,
			name='Sam',
			date_of_birth='2020-05-12',
		)
		self.client.force_login(self.parent_user)

		response = self.client.post(reverse('vaccination_add', args=[child.id]), {
			'vaccine_name': 'Example vaccine',
			'dose_number': 1,
			'scheduled_date': '2026-11-10',
			'hospital': hospital.id,
		})

		self.assertRedirects(response, reverse('parent_dashboard'))
		record = VaccinationRecord.objects.get(child=child)
		self.assertEqual(record.hospital, hospital)
		self.assertContains(self.client.get(reverse('parent_dashboard')), 'North Clinic')

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


class HospitalDashboardTests(TestCase):
	def setUp(self):
		self.hospital_user = CustomUser.objects.create_user(
			username='clinic-one',
			password='VaxCare-test-2026!',
			role='hospital',
		)
		self.hospital = Hospital.objects.create(user=self.hospital_user, name='North Clinic')
		self.other_hospital_user = CustomUser.objects.create_user(
			username='clinic-two',
			password='VaxCare-test-2026!',
			role='hospital',
		)
		self.other_hospital = Hospital.objects.create(
			user=self.other_hospital_user,
			name='South Clinic',
		)
		self.parent_user = CustomUser.objects.create_user(
			username='family-one',
			password='VaxCare-test-2026!',
			role='parent',
		)
		self.parent = Parent.objects.create(user=self.parent_user)

	def make_record(self, hospital, child_name):
		child = Child.objects.create(
			parent=self.parent,
			name=child_name,
			date_of_birth='2020-01-02',
		)
		return VaccinationRecord.objects.create(
			child=child,
			hospital=hospital,
			vaccine_name='Example vaccine',
			dose_number=1,
			scheduled_date='2026-11-10',
		)

	def test_hospital_dashboard_requires_hospital_login(self):
		response = self.client.get(reverse('hospital_dashboard'))

		self.assertEqual(response.status_code, 302)

	def test_hospital_only_sees_appointments_assigned_to_it(self):
		self.make_record(self.hospital, 'Assigned child')
		self.make_record(self.other_hospital, 'Other clinic child')
		self.client.force_login(self.hospital_user)

		response = self.client.get(reverse('hospital_dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'North Clinic appointment desk')
		self.assertContains(response, 'Assigned child')
		self.assertNotContains(response, 'Other clinic child')

	def test_assigned_hospital_can_confirm_appointment(self):
		record = self.make_record(self.hospital, 'Assigned child')
		self.client.force_login(self.hospital_user)

		response = self.client.post(
			reverse('hospital_mark_completed', args=[record.id]),
			{'administered_date': '2026-10-01'},
		)

		self.assertRedirects(response, reverse('hospital_dashboard'))
		record.refresh_from_db()
		self.assertEqual(record.status, VaccinationRecord.COMPLETED)
		self.assertEqual(record.completed_by_hospital, self.hospital)
		self.assertContains(self.client.get(reverse('hospital_dashboard')), 'Confirmed here')

	def test_hospital_profile_can_be_updated(self):
		self.client.force_login(self.hospital_user)

		response = self.client.post(reverse('hospital_profile_update'), {
			'name': 'North Clinic Main',
			'phone': '555-0190',
			'address': '10 Clinic Road',
		})

		self.assertRedirects(response, reverse('hospital_dashboard'))
		self.hospital.refresh_from_db()
		self.assertEqual(self.hospital.name, 'North Clinic Main')
		self.assertEqual(self.hospital.phone, '555-0190')
		self.assertEqual(self.hospital.address, '10 Clinic Road')

	def test_hospital_cannot_confirm_another_hospitals_appointment(self):
		record = self.make_record(self.other_hospital, 'Other clinic child')
		self.client.force_login(self.hospital_user)

		response = self.client.post(
			reverse('hospital_mark_completed', args=[record.id]),
			{'administered_date': '2026-10-01'},
		)

		self.assertEqual(response.status_code, 404)
		record.refresh_from_db()
		self.assertEqual(record.status, VaccinationRecord.SCHEDULED)

	def test_hospital_cannot_confirm_with_a_future_date(self):
		record = self.make_record(self.hospital, 'Assigned child')
		self.client.force_login(self.hospital_user)

		response = self.client.post(
			reverse('hospital_mark_completed', args=[record.id]),
			{'administered_date': '2099-01-01'},
		)

		self.assertRedirects(response, reverse('hospital_dashboard'))
		record.refresh_from_db()
		self.assertEqual(record.status, VaccinationRecord.SCHEDULED)

	def test_parent_cannot_open_hospital_dashboard(self):
		self.client.force_login(self.parent_user)

		response = self.client.get(reverse('hospital_dashboard'))

		self.assertEqual(response.status_code, 403)

	def test_hospital_registration_saves_facility_details(self):
		response = self.client.post(reverse('register_hospital'), {
			'username': 'new-clinic',
			'email': 'clinic@example.test',
			'name': 'East Clinic',
			'phone': '555-0188',
			'address': '25 Health Avenue',
			'password1': 'Unique-VaxCare-Test-2026!',
			'password2': 'Unique-VaxCare-Test-2026!',
		})

		self.assertRedirects(response, reverse('hospital_dashboard'))
		hospital = Hospital.objects.get(user__username='new-clinic')
		self.assertEqual(hospital.name, 'East Clinic')
		self.assertEqual(hospital.phone, '555-0188')
		self.assertEqual(hospital.address, '25 Health Avenue')
