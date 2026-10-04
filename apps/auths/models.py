from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db.models import (
    BooleanField,
    CharField,
    EmailField,
)


class CustomUserManager(BaseUserManager):
    """Custom user manager to make database requests"""
    
    def create_user(
        self, 
        email: str, 
        first_name: str,
        last_name: str,
        password: str,
        **extra_fields
        ) -> 'CustomUser':
        """Create custom user"""
        if not email:
            raise ValueError("Email is required")
        
        user = self.model(
            email = self.normalize_email(email),
            first_name = first_name,
            last_name = last_name,
            **extra_fields
        )
        
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(
        self, 
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        **extra_fields
        ) -> 'CustomUser':
        """Create superuser. Used by manage.py createsuperuser"""
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        user = self.create_user(
            email,
            first_name,
            last_name,
            password,
            **extra_fields)
        
        # user.is_staff = True
        # user.is_superuser = True
        
        # user.save(self._db)
        
        return user
        

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model extending AbstractBaseModel"""
    
    NAME_MAX_LEN = 50
    
    email = EmailField(
        unique=True,
    )
    first_name = CharField(
        max_length=NAME_MAX_LEN,
    )
    last_name = CharField(
        max_length=NAME_MAX_LEN,
    )
    is_active = BooleanField(
        default=True,
    )
    is_staff = BooleanField(
        default=False
    )
    
    REQUIRED_FIELDS = ("first_name", "last_name")
    USERNAME_FIELD = "email"
    
    objects = CustomUserManager()
    
