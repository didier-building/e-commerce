from django.shortcuts import render


def payment_success(request):
    session_id = request.GET.get('session_id')
    return render(request, 'payments/success.html', {'session_id': session_id})

def payment_cancel(request):
    return render(request, 'payments/cancel.html')