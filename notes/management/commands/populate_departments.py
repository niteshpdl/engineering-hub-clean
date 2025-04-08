from django.core.management.base import BaseCommand
from notes.models import Department, Semester

class Command(BaseCommand):
    help = 'Populates the database with departments and semesters'

    def handle(self, *args, **kwargs):
        # Define departments and their semesters
        departments = [
            {"name": "Civil Engineering", "description": "Civil Engineering Course Structure", "semesters": 8},
            {"name": "Computer Engineering", "description": "Computer Engineering Course Structure", "semesters": 8},
            {"name": "Electronics, Communication and Information Engineering", "description": "Electronics, Communication and Information Engineering Course Structure", "semesters": 8},
            {"name": "Electrical Engineering", "description": "Electrical Engineering Course Structure", "semesters": 8},
            {"name": "Mechanical Engineering", "description": "Mechanical Engineering Course Structure", "semesters": 8},
            {"name": "Aerospace Engineering", "description": "Aerospace Engineering Course Structure", "semesters": 8},
            {"name": "Chemical Engineering", "description": "Chemical Engineering Course Structure", "semesters": 8},
            {"name": "Architecture", "description": "Architecture Course Structure", "semesters": 10},
            {"name": "Industrial Engineering", "description": "Industrial Engineering Course Structure", "semesters": 8},
            {"name": "Agricultural Engineering", "description": "Agricultural Engineering Course Structure", "semesters": 8},
            {"name": "Automobile Engineering", "description": "Automobile Engineering Course Structure", "semesters": 8},
            {"name": "Geomatics Engineering", "description": "Geomatics Engineering Course Structure", "semesters": 8},
        ]
        
        # Create departments and semesters
        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                name=dept_data["name"],
                defaults={"description": dept_data["description"]}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department: {dept.name}'))
            else:
                self.stdout.write(f'Department already exists: {dept.name}')
            
            # Create semesters for each department - removed 'name' field
            for i in range(1, dept_data["semesters"] + 1):
                sem, created = Semester.objects.get_or_create(
                    department=dept,
                    number=i,
                    # No 'defaults' with 'name' field since it doesn't exist
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  - Created semester {i} for {dept.name}'))
                else:
                    self.stdout.write(f'  - Semester {i} already exists for {dept.name}')
