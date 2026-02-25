from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from dashboard.models import Comment, Station, Reply, Tour, Stop, Task
import json
from django.utils import timezone

class CommentConsumer(WebsocketConsumer):
    group_name = 'dashboard_chat_group'
    channel_name = 'dashboard_chat_channel'

    user = None

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

        if not self.scope["user"].is_authenticated:
            self.send_error(f'You must be logged in')
            self.close()
            return
        
        self.user = self.scope["user"]

        self.broadcast_comment()
        self.broadcast_reply()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
    
    def receive(self, **kwargs):
        print("in recieve")
        if 'text_data' not in kwargs:
            self.send_error('you must send text_data')
            return
        
        try:
            data = json.loads(kwargs['text_data'])
        except json.JSONDecoder:
            self.send_error('invalid JSON sent to server')
            return

        if 'action' not in data:
            self.send_error('action property not sent in JSON')
            return

        action = data['action']

        if action == 'add_comment':
            self.received_add_comment(data)
            return
        
        if action == 'add_reply':
            self.received_add_reply(data)
            return
        
    def received_add_comment(self, data):
        if 'text' not in data:
            self.send_error('"text" property not sent in JSON')
            return
        
        text = data['text']
        stationId = data['id']
        station = Station.objects.filter(id=stationId).first()
        new_comment = Comment(commented_to=station, commentor=self.user, content=text, name = self.user.first_name, creation_time=timezone.now())
        new_comment.save()
        
        self.broadcast_comment()

    def received_add_reply(self, data):
        if 'text' not in data:
            self.send_error('"text" property not sent in JSON')
            return
        
        text = data['text']
        commentId = data['id']
        comment = Comment.objects.filter(id=commentId).first()
        new_reply = Reply(reply_to=comment, replier=self.user, content=text, name = self.user.first_name, creation_time=timezone.now())
        new_reply.save()
        
        self.broadcast_reply()
    
    def broadcast_comment(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(Comment.make_comment_list())
            }
        )
    
    def broadcast_reply(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(Reply.make_reply_list())
            }
        )

    def broadcast_event(self, event):
        self.send(text_data=event['message'])
    

class TourConsumer(WebsocketConsumer):
    group_name = 'dashboard_tour_group'
    channel_name = 'dashboard_tour_channel'

    user = None

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

        if not self.scope["user"].is_authenticated:
            self.send_error(f'You must be logged in')
            self.close()
            return
        
        self.user = self.scope["user"]
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
    
    def receive(self, **kwargs):
        if 'text_data' not in kwargs:
            self.send_error('you must send text_data')
            return
        
        try:
            data = json.loads(kwargs['text_data'])
        except json.JSONDecoder:
            self.send_error('invalid JSON sent to server')
            return

        if 'action' not in data:
            self.send_error('action property not sent in JSON')
            return

        action = data['action']

        if action == 'create_tour':
            self.received_create_tour(data)
            return
        
        if action == 'add_stop':
            self.received_add_stop(data)
            return
        
        if action == 'add_task':
            self.received_add_task(data)
            return
    
    def received_create_tour(self,data):

        if (('date' not in data) and ('user' not in data)):
            self.send_error('missing json properties')
            return
        
        date = data['date']
        user = data['user']
        
        new_tour = Tour(due_date=date, assigned_to=user)
        new_tour.save()

        return
    
    def received_add_stop(self,data):

        if (('tour_id' not in data) and ('station_id' not in data) and ('order' not in data)):
            self.send_error('missing json properties')
            return
        
        tour_id = data['tour_id']
        station_id = data['station_id']
        order = data['order']

        tour = Tour.objects.filter(id=tour_id).first()
        station = Station.objects.filter(id=station_id).first()

        new_stop = Stop(tour=tour, station=station, order=order)
        new_stop.save()

        return 
    
    def received_add_task(self, data):

        if (('stop_id' not in data) and ('text' not in data)):
            self.send_error('missing json properties')
            return
        
        stop_id = data['stop_id']
        content = data['text']

        stop = Stop.objects.filter(id=stop_id).first()

        new_task = Task(stop=stop, content=content)
        new_task.save()

        return
    
    def broadcast_tour(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(Tour.make_tour_list())
            }
        )
    
    def broadcast_stop(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(Stop.make_stop_list())
            }
        )
    
    def broadcast_task(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(Task.make_task_list())
            }
        )