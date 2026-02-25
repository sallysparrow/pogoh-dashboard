from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Station(models.Model):
	name = models.CharField(max_length=200)
	latitude = models.DecimalField(max_digits=9, decimal_places=6)
	longitude = models.DecimalField(max_digits=9, decimal_places=6)
	slots = models.IntegerField()
     
	def __str__(self):
		return f'Station(id = {self.id}): name = {self.name}, latitude = {self.latitude}, longitude = {self.longitude}, slots = {self.slots}'
       
class StationStatusLog(models.Model):
    date = models.DateField()
    time = models.TimeField()
    empty_slots = models.IntegerField()
    free_bikes = models.IntegerField()
    empty = models.BooleanField()
    full = models.BooleanField()
    station = models.ForeignKey(Station, on_delete=models.PROTECT)
    
    def __str__(self):
          return f'StationStatusLog(id = {self.id}, empty = {self.empty}, full = {self.full})'
         
class Comment(models.Model):
    commented_to = models.ForeignKey(Station, on_delete=models.PROTECT)
    commentor = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.CharField(max_length=200)
    name = models.CharField(max_length=20)
    creation_time = models.DateTimeField()

    def __str__(self):
        return f'Comment(id={self.id}): commented_by={self.posted_by}'
    
    @classmethod
    def make_comment_list(cls):
        comment_dict_list = []
        for comment in cls.objects.all():
            comment_dict = {
                'id': comment.id,
                'commented_to_id': comment.commented_to.id,
                'commentor': comment.commentor.first_name,
                'content': comment.content,
                'name': comment.commentor.first_name,
                'creation_time': comment.creation_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            comment_dict_list.append(comment_dict)
        return comment_dict_list
    
class Reply(models.Model):
    reply_to = models.ForeignKey(Comment, on_delete=models.PROTECT)
    replier = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.CharField(max_length=200)
    name = models.CharField(max_length=20)
    creation_time = models.DateTimeField()

    def __str__(self):
        return f'Reply(id={self.id}): replier={self.replier.first_name}'
    
    @classmethod
    def make_reply_list(cls):
        reply_dict_list = []
        for reply in cls.objects.all():
            reply_dict = {
                'id': reply.id,
                'replied_to_id': reply.reply_to.id,
                'replier': reply.replier.first_name,
                'content': reply.content,
                'name': reply.replier.first_name,
                'creation_time': reply.creation_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            reply_dict_list.append(reply_dict)
        return reply_dict_list
    
class Tour(models.Model):
    due_date = models.DateField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
         return f'Tour(id = {self.id}): due_date = {self.due_date}, assigned_to = {self.assigned_to}'
    
    @classmethod
    def make_tour_list(cls):
        tour_dict_list = []
        for tour in cls.objects.all():
            tour_dict = {
                'id': tour.id,
                'due_date': tour.due_date.strftime("%Y-%m-%d"),
                'assigned_to': tour.assigned_to.first_name
            }
            tour_dict_list.append(tour_dict)
        return tour_dict_list
     
class Stop(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'Stop(id = {self.id}): tour_id = {self.tour.id}, station_name = {self.station.name}'
    
    @classmethod
    def make_stop_list(cls):
        stop_dict_list = []
        for stop in cls.objects.all():
            stop_dict = {
                'id': stop.id,
                'tour_id': stop.tour.id,
                'tour_date': stop.tour.date,
                'station_name': stop.station.name,
                'order': stop.order,
            }
            stop_dict_list.append(stop_dict)
        return stop_dict_list
     
class Task(models.Model):
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    content = models.CharField(max_length=400)

    def __str__(self):
         return f'Task(id = {self.id}): stop = {self.stop.id}, content = {self.content}'
    
    @classmethod
    def make_task_list(cls):
        task_dict_list = []
        for task in cls.objects.all():
            task_dict = {
                'id': task.id,
                'stop_order': task.stop.order,
                'stop_name': task.stop.name,
                'content': task.content,
            }
            task_dict_list.append(task_dict)
        return task_dict_list

class StationSnapshot(models.Model):
    """
    One row per scrape of a station's status.
    """
    station      = models.ForeignKey(
        Station,
        related_name="snapshots",
        on_delete=models.CASCADE,
    )
    timestamp    = models.DateTimeField(db_index=True)
    free_bikes   = models.PositiveSmallIntegerField()
    empty_slots  = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"
        constraints = [
            # Prevent duplicate rows for the same scrape
            models.UniqueConstraint(
                fields=["station", "timestamp"],
                name="uniq_station_timestamp",
            )
        ]

    def __str__(self):
        return f"{self.station.name} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"