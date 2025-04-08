from notes.models import Department, Semester

departments = [
    {"name": "Aerospace", "description": "Aerospace Engineering"},
    {"name": "Agricultural", "description": "Agricultural Engineering"},
    {"name": "Automobile", "description": "Automobile Engineering"},
    {"name": "Chemical", "description": "Chemical Engineering"},
    {"name": "Civil", "description": "Civil Engineering"},
    {"name": "Computer", "description": "Computer Engineering"},
    {"name": "Electrical", "description": "Electrical Engineering"},
    {"name": "Electronics Communication and Information", "description": "Electronics Communication and Information Engineering"},
    {"name": "Geomatics", "description": "Geomatics Engineering"},
    {"name": "Industrial", "description": "Industrial Engineering"},
    {"name": "Mechanical", "description": "Mechanical Engineering"},
    {"name": "Architecture", "description": "Architecture"}
]

for dept_info in departments:
    department, created = Department.objects.get_or_create(
        name=dept_info["name"],
        defaults={"description": dept_info["description"]}
    )
    
    if not created and not department.description:
        department.description = dept_info["description"]
        department.save()
        
    if dept_info["name"] == "Architecture":
        semesters = range(1, 11)  # 10 semesters for Architecture
    else:
        semesters = range(1, 9)  # 8 semesters for other departments
    
    for sem in semesters:
        Semester.objects.get_or_create(department=department, number=sem)
