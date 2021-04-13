from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.forms.utils import ErrorList
from .models import MusicPlaylist, Video
from .forms import VideoForm, SearchForm
import urllib
import requests


def home(request):
    recent_playlists = MusicPlaylist.objects.all().order_by('-id')[:3]
    popular_playlists = MusicPlaylist.objects.all()
    return render(request, 'topmusicapp/home.html', {'recent_playlists': recent_playlists, 'popular_playlists': popular_playlists})


@login_required
def dashboard(request):
    playlists = MusicPlaylist.objects.filter(user=request.user)
    return render(request, 'topmusicapp/dashboard.html', {'playlists': playlists})


@login_required
def add_video(request, pk):
    form = VideoForm()
    search_form = SearchForm()
    playlist = MusicPlaylist.objects.get(pk=pk)
    if not playlist.user == request.user:
        raise Http404

    if request.method == "POST":
        form = VideoForm(request.POST)
        if form.is_valid():
            video = Video()
            video.playlist = playlist
            video.url = form.cleaned_data['url']
            parsed_url = urllib.parse.urlparse(video.url)
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v')
            if video_id:
                video.youtube_id = video_id[0]
                response = requests.get(
                    f'https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id={video_id[0]}&key={YOUTUBE_API_KEY}')
                json = response.json()
                title = json['items'][0]['snippet']['title']
                video.title = title
                video.save()
                return redirect('detail_playlist', pk)
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('Needs to be a Youtube url')
    return render(request, 'topmusicapp/addvideo.html', {'form': form, 'search_form': search_form, 'playlist': playlist})


@login_required
def video_search(request):
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        encoded_search_term = urllib.parse.quote(
            search_form.cleaned_data['search_term'])
        response = requests.get(
            f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q={encoded_search_term}&key={YOUTUBE_API_KEY}')
        return JsonResponse(response.json())
    return JsonResponse({'error': 'Not able to validate form'})


class DeleteVideo(LoginRequiredMixin, generic.DeleteView):
    model = Video
    template_name = 'topmusicapp/deletevideo.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        video = super(DeleteVideo, self).get_object()
        if not video.playlist.user == self.request.user:
            raise Http404
        return video


class SignUp(generic.CreateView):
    # passes it to the template as 'form' which you can then use there
    form_class = UserCreationForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get(
            'username'), form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return view


class CreatePlaylist(LoginRequiredMixin, generic.CreateView):
    model = MusicPlaylist
    fields = ['title']
    template_name = 'topmusicapp/createplaylist.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        super(CreatePlaylist, self).form_valid(form)
        return redirect('dashboard')


class DetailPlaylist(generic.DetailView):
    model = MusicPlaylist
    template_name = 'topmusicapp/detailplaylist.html'


class UpdatePlaylist(LoginRequiredMixin, generic.UpdateView):
    model = MusicPlaylist
    template_name = 'topmusicapp/updateplaylist.html'
    fields = ['title']
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        musicplaylist = super(UpdatePlaylist, self).get_object()
        if not musicplaylist.user == self.request.user:
            raise Http404
        return musicplaylist


class DeletePlaylist(LoginRequiredMixin, generic.DeleteView):
    model = MusicPlaylist
    template_name = 'topmusicapp/deleteplaylist.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        musicplaylist = super(DeletePlaylist, self).get_object()
        if not musicplaylist.user == self.request.user:
            raise Http404
        return musicplaylist
