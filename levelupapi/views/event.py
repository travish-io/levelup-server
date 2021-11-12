from django.core.exceptions import ValidationError
from rest_framework import status
from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from levelupapi.models import Event, Game, Gamer
from rest_framework.decorators import action


class EventView(ViewSet):
    """Level up events"""

    def list(self, request):
        """Handle GET requests to events resource

        Returns:
            Response -- JSON serialized list of events
        """
        # Get the current authenticated user
        gamer = Gamer.objects.get(user=request.auth.user)
        events = Event.objects.all()

        # Set the `joined` property on every event
        for event in events:
            # Check to see if the gamer is in the attendees list on the event
            event.joined = gamer in event.attendees.all()

        # Support filtering events by game
        game = self.request.query_params.get('gameId', None)
        if game is not None:
            events = events.filter(game__id=type)

        serializer = EventSerializer(
            events, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single event

        Returns:
            Response -- JSON serialized event instance
        """
        try:
            # `pk` is a parameter to this function, and
            # Django parses it from the URL route parameter
            #   http://localhost:8000/events/2
            #
            # The `2` at the end of the route becomes `pk`
            event = Event.objects.get(pk=pk)
            serializer = EventSerializer(event, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def create(self, request):
        """Handle POST operations

        Returns:
            Response -- JSON serialized game instance
        """

        # Uses the token passed in the `Authorization` header
        game = Game.objects.get(pk=request.data["gameId"])

        # Use the Django ORM to get the record from the database
        # whose `id` is what the client passed as the
        # `gameTypeId` in the body of the request.
        organizer = Gamer.objects.get(user=request.auth.user)

        # Try to save the new game to the database, then
        # serialize the game instance as JSON, and send the
        # JSON as a response to the client request
        try:
            # Create a new Python instance of the Game class
            # and set its properties from what was sent in the
            # body of the request from the client.
            event = Event.objects.create(
                description=request.data["description"],
                date=request.data["date"],
                time=request.data["time"],
                game=game,
                organizer=organizer

            )
            serializer = EventSerializer(event, context={'request': request})
            return Response(serializer.data)

        # If anything went wrong, catch the exception and
        # send a response with a 400 status code to tell the
        # client that something was wrong with its request data
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Handle PUT requests for a event

        Returns:
            Response -- Empty body with 204 status code
        """
        organizer = Gamer.objects.get(user=request.auth.user)

        game = Game.objects.get(pk=request.data["gameId"])

        # Do mostly the same thing as POST, but instead of
        # creating a new instance of Game, get the game record
        # from the database whose primary key is `pk`
        event = Event.objects.get(pk=pk)
        event.description = request.data["description"]
        event.date = request.data["date"]
        event.time = request.data["time"]
        event.game = game
        event.organizer = organizer
        event.attendees = request.data["attendees"]

        # 204 status code means everything worked but the
        # server is not sending back any data in the response
        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single event

        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            event = Event.objects.get(pk=pk)
            event.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Event.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['post', 'delete'], detail=True)
    def signup(self, request, pk=None):
        """Managing gamers signing up for events"""
        # Django uses the `Authorization` header to determine
        # which user is making the request to sign up
        gamer = Gamer.objects.get(user=request.auth.user)

        try:
            # Handle the case if the client specifies a game
            # that doesn't exist
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {'message': 'Event does not exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # A gamer wants to sign up for an event
        if request.method == "POST":
            try:
                # Using the attendees field on the event makes it simple to add a gamer to the event
                # .add(gamer) will insert into the join table a new row the gamer_id and the event_id
                event.attendees.add(gamer)
                return Response({}, status=status.HTTP_201_CREATED)
            except Exception as ex:
                return Response({'message': ex.args[0]})

        # User wants to leave a previously joined event
        elif request.method == "DELETE":
            try:
                # The many to many relationship has a .remove method that removes the gamer from the attendees list
                # The method deletes the row in the join table that has the gamer_id and event_id
                event.attendees.remove(gamer)
                return Response(None, status=status.HTTP_204_NO_CONTENT)
            except Exception as ex:
                return Response({'message': ex.args[0]})


class EventSerializer(serializers.ModelSerializer):
    """JSON serializer for events

    Arguments:
        serializer type
    """
    joined = serializers.BooleanField(required=False)

    class Meta:
        model = Event
        fields = ('id', 'description', 'date', 'time',
                  'game', 'organizer', 'attendees', 'joined')
        depth = 1
