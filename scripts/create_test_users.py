import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_chatbot.settings')
django.setup()

from django.contrib.auth.models import User

def ensure_users():
    created = []

    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass123')
        try:
            admin.profile.role = 'admin'
            admin.profile.save()
        except Exception:
            pass
        created.append('admin')

    if not User.objects.filter(username='customer').exists():
        cust = User.objects.create_user('customer', 'customer@example.com', 'custpass123')
        try:
            cust.profile.role = 'customer'
            cust.profile.save()
        except Exception:
            pass
        created.append('customer')

    if created:
        print('Created users:', ', '.join(created))
    else:
        print('Users already exist')

if __name__ == '__main__':
    ensure_users()
