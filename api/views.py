from django.shortcuts import render

# Create your views here.
from ninja import NinjaAPI

api = NinjaAPI()

@api.get("/hello")
def hello(request):
    return {"message": "Hello from Nahjez API"}