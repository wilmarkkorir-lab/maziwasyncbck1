from django.db import models

# Create your modeles here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # This are customer user model with roled bassed access
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('porter', 'Porter'),
        ('farmer', 'Farmer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES , default='farmer')
    phone_number= models.CharField(max_length=15, unique=True, blank=True, null=True)
    def __str__(self):
        return f"{self.username ,{self.role}}"


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class FarmerProfile(BaseModel):
    # complete farmer profile with farm details
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    national_id = models.CharField(max_length=15, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender=models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')])

    # contact information
    phone_number = models.CharField(max_length=15, unique=True)
    alternative_phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # farm information
    farm_name = models.CharField(max_length=200,blank=True, null=True)
    farm_size_acres = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    number_of_cows= models.IntegerField(default=0)
    membership_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)
    mpesa_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    # stats auto updated by the system
    total_milk_delivered = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)


  

    def __str__(self):
        return f"{self.first_name} {self.last_name} "

# =====================================
#porters profile model
# =====================================

class PorterProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='porter_profile')
    profile_image = models.ImageField(upload_to='porter/profiles', blank=True, null=True)
    employee_id = models.CharField(max_length=20, unique=True)
    national_id = models.CharField(max_length=15, unique=True)
    first_name = models.CharField(max_length=100)
    phone_number=models.CharField(max_length=15, unique=True ,blank=True, null=True)
    last_name = models.CharField(max_length=100)
    route_name = models.CharField(max_length=200)
    assigned_farmers = models.ManyToManyField(FarmerProfile, related_name='assigned_porters', blank=True)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    total_collections = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_litres_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)


    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.employee_id}"
    
# ===========================
# milk collection model
# ===========================

class MilkCollection(BaseModel):
    # daily milk collection record for each farmer
    SESSIONS = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    ]
# why use foreign key to link the milk collection to the farmer and porter profiles
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='milk_collections')
    porter = models.ForeignKey(PorterProfile, on_delete=models.CASCADE, related_name='milk_collections')
    litres=models.DecimalField(max_digits=10, decimal_places=2)
    session = models.CharField(max_length=10, choices=SESSIONS)
    collection_date = models.DateField(auto_now_add=True)
    price_per_litre = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.collection_date} : {self.farmer.first_name} {self.farmer.last_name} - {self.litres} litres"
    def save(self, *args, **kwargs):
        # Calculate total amount based on litres and price per litre
        self.total_amount = self.litres * self.price_per_litre
        super().save(*args, **kwargs)

# feedback model for (Base Model)
class Feedback(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    ]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='feedback')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True ,default='pending')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, )
    
    def __str__(self):
        return f"{self.farmer} - {self.status}"


# ==========================
# notices
# =========================
class Notice(BaseModel):
    TARGET_CHOICES = [
        ('all', 'All Users'),
        ('farmers', 'Farmers Only'),
        ('porters', 'Porters Only'),
        
    ]
    title=models.CharField(max_length=200)
    message=models.TextField()
    target=models.CharField(max_length=50, choices=TARGET_CHOICES )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_important = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
# ==========================
# payment model
# ==========================
class Payment(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
    ]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    originator_conversation_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    transaction_ref = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_ref}-KES {self.amount}"

    



 


   
