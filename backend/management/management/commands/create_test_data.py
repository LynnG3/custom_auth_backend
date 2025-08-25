from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

from permissions.models import Role, UserRole, ResourceType, RolePermission
from mock_resources.models import Resource

User = get_user_model()


class Command(BaseCommand):
    """Команда для создания набора тестовых данных."""
    
    help = 'Создает набор тестовых данных: пользователи, роли, ресурсы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед созданием',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очистка существующих данных...')
            self.clear_data()
        
        self.stdout.write('Создание набора тестовых данных...')
        
        with transaction.atomic():
            # 1. Создает роли
            roles = self.create_roles()
            
            # 2. Создает типы ресурсов
            resource_types = self.create_resource_types()
            
            # 3. Создает пользователей
            users = self.create_users()
            
            # 4. Назначает роли пользователям
            self.assign_roles_to_users(users, roles)
            
            # 5. Настраивает разрешения для ролей
            self.setup_role_permissions(roles, resource_types)
            
            # 6. Создает моковые ресурсы
            self.create_mock_resources(users, resource_types)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Набор тестовых данных успешно создан!')
        )
        self.print_summary(users, roles, resource_types)

    def create_roles(self):
        """Создает роли пользователей."""
        self.stdout.write('Создание ролей...')
        
        roles = {}
        roles_data = [
            {'name': 'admin', 'description': 'Администратор системы'},
            {'name': 'manager', 'description': 'Менеджер'},
            {'name': 'user', 'description': 'Обычный пользователь'},
            {'name': 'guest', 'description': 'Гость'},
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            roles[role.name] = role
            status = 'создана' if created else 'уже существует'
            self.stdout.write(f'    - Роль "{role.name}": {status}')
        
        return roles

    def create_resource_types(self):
        """Создает типы ресурсов."""
        self.stdout.write('Создание типов ресурсов...')
        
        resource_types = {}
        types_data = [
            {'name': 'product', 'description': 'Товары и услуги'},
            {'name': 'order', 'description': 'Заказы пользователей'},
        ]
        
        for type_data in types_data:
            resource_type, created = ResourceType.objects.get_or_create(
                name=type_data['name'],
                defaults=type_data
            )
            resource_types[resource_type.name] = resource_type
            status = 'создан' if created else 'уже существует'
            self.stdout.write(f'    - Тип ресурса "{resource_type.name}": {status}')
        
        return resource_types

    def create_users(self):
        """Создает тестовых пользователей."""
        self.stdout.write('Создание пользователей...')
        
        users = {}
        users_data = [
            {
                'email': 'admin@example.com',
                'first_name': 'Админ',
                'last_name': 'Системы',
                'password': 'AdminPass123!',
                'role': 'admin'
            },
            {
                'email': 'manager@example.com',
                'first_name': 'Менеджер',
                'last_name': 'Отдела',
                'password': 'ManagerPass123!',
                'role': 'manager'
            },
            {
                'email': 'user@example.com',
                'first_name': 'Пользователь',
                'last_name': 'Обычный',
                'password': 'UserPass123!',
                'role': 'user'
            },
        ]
        
        for user_data in users_data:
            email = user_data['email']
            role_name = user_data.pop('role')
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults=user_data
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
            
            users[role_name] = user
            status = 'создан' if created else 'уже существует'
            self.stdout.write(f'    - Пользователь {email}: {status}')
        
        return users

    def assign_roles_to_users(self, users, roles):
        """Назначает роли пользователям."""
        self.stdout.write('Назначение ролей пользователям...')
        
        for role_name, user in users.items():
            role = roles[role_name]
            
            # Удаляет существующие роли пользователя
            UserRole.objects.filter(user=user).delete()
            
            # Назначает новую роль
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={'assigned_by': user, 'is_active': True}
            )
            
            status = 'назначена' if created else 'уже назначена'
            self.stdout.write(f'    - Роль "{role.name}" пользователю {user.email}: {status}')

    def setup_role_permissions(self, roles, resource_types):
        """Настраивает разрешения для ролей."""
        self.stdout.write('Настройка разрешения для ролей...')
        
        # Базовые разрешения для каждой роли
        permissions_config = {
            'admin': {
                'can_read': True,
                'can_create': True,
                'can_update': True,
                'can_delete': True,
                'can_manage_others': True
            },
            'manager': {
                'can_read': True,
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_manage_others': False
            },
            'user': {
                'can_read': True,
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_manage_others': False
            },
            'guest': {
                'can_read': True,
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_manage_others': False
            }
        }
        
        # Специальные разрешения для пользователя на заказы
        user_order_permissions = {
            'can_read': True,
            'can_create': True,
            'can_update': True,
            'can_delete': False,
            'can_manage_others': False
        }
        
        for role_name, role in roles.items():
            for resource_type_name, resource_type in resource_types.items():
                # Получает или создает разрешение
                permission, created = RolePermission.objects.get_or_create(
                    role=role,
                    resource_type=resource_type,
                    defaults=permissions_config[role_name]
                )
                
                # Обновляет разрешения
                base_permissions = permissions_config[role_name]
                
                # Специальная логика для пользователя и заказов
                if role_name == 'user' and resource_type_name == 'order':
                    for key, value in user_order_permissions.items():
                        setattr(permission, key, value)
                else:
                    for key, value in base_permissions.items():
                        setattr(permission, key, value)
                
                permission.save()
                
                status = 'создано' if created else 'обновлено'
                self.stdout.write(
                    f'    - Разрешения для роли "{role.name}" на ресурс "{resource_type.name}": {status}'
                )

    def create_mock_resources(self, users, resource_types):
        """Создает моковые ресурсы."""
        self.stdout.write('Создание моковых ресурсов...')
        
        # Создает продукты
        product_resource = Resource.objects.create(
            name='Тестовый продукт',
            resource_type=resource_types['product'],
            owner=users['manager']
        )
        self.stdout.write(f'    - Продукт "{product_resource.name}" создан пользователем {product_resource.owner.email}')
        
        # Создает заказ
        order_resource = Resource.objects.create(
            name='Тестовый заказ',
            resource_type=resource_types['order'],
            owner=users['user']
        )
        self.stdout.write(f'    - Заказ "{order_resource.name}" создан пользователем {order_resource.owner.email}')

    def clear_data(self):
        """Очищает существующие данные."""
        self.stdout.write('Очистка данных...')
        
        # Очищает в правильном порядке (из-за внешних ключей)
        Resource.objects.all().delete()
        self.stdout.write('    - Ресурсы удалены')
        
        RolePermission.objects.all().delete()
        self.stdout.write('    - Разрешения удалены')
        
        UserRole.objects.all().delete()
        self.stdout.write('    - Связи пользователь-роль удалены')
        
        # Оставляем пользователей, роли и типы ресурсов (могут использоваться в других местах)
        self.stdout.write('    - Пользователи, роли и типы ресурсов оставлены')

    def print_summary(self, users, roles, resource_types):
        """Выводит сводку созданных данных."""
        self.stdout.write('\n Сводка созданных данных:')
        self.stdout.write('=' * 50)
        
        self.stdout.write(f'Пользователи: {len(users)}')
        for role_name, user in users.items():
            self.stdout.write(f'  - {role_name}: {user.email}')
        
        self.stdout.write(f'Роли: {len(roles)}')
        for role_name, role in roles.items():
            self.stdout.write(f'  - {role_name}: {role.description}')
        
        self.stdout.write(f'Типы ресурсов: {len(resource_types)}')
        for type_name, resource_type in resource_types.items():
            self.stdout.write(f'  - {type_name}: {resource_type.description}')
        
        self.stdout.write(f'Моковые ресурсы: 2')
        self.stdout.write('  - Тестовый продукт (product)')
        self.stdout.write('  - Тестовый заказ (order)')
        
        self.stdout.write('\n Логины для тестирования:')
        self.stdout.write('  - admin@example.com / AdminPass123!')
        self.stdout.write('  - manager@example.com / ManagerPass123!')
        self.stdout.write('  - user@example.com / UserPass123!')
