from django.shortcuts import render, redirect
from datetime import date


def home(request):
    return render(request, 'home.html')


def dashboard_view(request):

    try:
        return render(request, 'Pdashboard.html')
    except Exception as e:
        # This will print the exact error to your terminal if it fails
        print(f"DEBUG: Dashboard template error: {e}")
        # As a fallback, reload the home page so you don't get a crash
        return redirect('home')
    


temporary_children_list = []

def dashboard_view(request):
    if request.method == "POST":
        # 1. Get the data
        name = request.POST.get('child_name')
        vaccine = request.POST.get('vaccine')
        dob = request.POST.get('dob')
        
        # 2. Save it to the list
        temporary_children_list.append({
            'name': name,
            'vaccine': vaccine,
            'date': dob,
        })

        return redirect('parent_dashboard') 

    # If it's a normal GET request (like a refresh), just show the list
    return render(request, 'Pdashboard.html', {'children': temporary_children_list})


# Make sure this name matches what is in urls.py EXACTLY
def add_child_view(request):
    return render(request, 'add_child.html')


def remove_child_view(request, index):
    if request.method == "POST":
        try:
            temporary_children_list.pop(index)
        except IndexError:
            pass
    return redirect('parent_dashboard')