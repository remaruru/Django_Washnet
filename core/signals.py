from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, CustomerProfile, EmployeeProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.RoleChoices.CUSTOMER:
            CustomerProfile.objects.create(user=instance)
        elif instance.role == User.RoleChoices.EMPLOYEE:
            EmployeeProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.role == User.RoleChoices.CUSTOMER:
        if hasattr(instance, 'customer_profile'):
            instance.customer_profile.save()
    elif instance.role == User.RoleChoices.EMPLOYEE:
        if hasattr(instance, 'employee_profile'):
            instance.employee_profile.save()
