from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from mailing.models import Recipient


class RecipientListView(ListView):
    model = Recipient
    context_object_name = 'recipients'

    # def get_queryset(self):
    #     queryset = cache.get('products_queryset')
    #     if not queryset:
    #         queryset = super().get_queryset()
    #         cache.set('products_queryset', queryset, 60 * 15)
    #     return queryset

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['categories'] = Category.objects.all()
    #     return context

# @method_decorator(cache_page(60 * 15), name='dispatch')
class RecipientDetailView(DetailView):
    model = Recipient

class RecipientCreateView(CreateView):
    model = Recipient
    form_class = RecipientForm
    success_url = reverse_lazy("mailing:recipient_list")

    # def form_valid(self, form):
    #     form.instance.owner = self.request.user
    #     return super().form_valid(form)

class RecipientUpdateView(UpdateView):
    model = Recipient
    form_class = RecipientForm
    success_url = reverse_lazy("mailing:recipient_list")

    def get_success_url(self):
        return reverse("mailing:recipient_detail", args=[self.kwargs.get('pk')])


class RecipientDeleteView(DeleteView):
    model = Recipient
    success_url = reverse_lazy("mailing:recipient_list")
