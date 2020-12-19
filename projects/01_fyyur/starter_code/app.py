#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean(), nullable=False, default=False)
    seeking_description = db.Column(db.String(2000))
    shows = db.relationship('Show', backref='venue',lazy='dynamic')


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(2000))
    shows = db.relationship('Show', backref='artist',lazy='dynamic')

    def insert(self):
        db.session.add(self)
        db.session.commit()
    
    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<Aritst {self.id} {self.name}>'
    

class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  try:
    # Get distinct city & states
    city_states = Venue.query.with_entities(Venue.city, Venue.state).distinct()
    data = []
    # Get the venues per pair of City & state
    for city_state in city_states:
      #Query all the venues for the given city & state combination
      venues_with_attributes = []
      venues = Venue.query.filter(
        Venue.city==city_state.city, Venue.state==city_state.state
        ).all()
      for venue in venues:
        upcoming_shows = venue.shows.filter(Show.start_time > datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()
        venues_with_attributes.append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(upcoming_shows)
        })
      #Query and append number of upcoming shows in each venue
      data.append({
        "city": city_state.city,
        "state": city_state.state,
        "venues": venues_with_attributes
      })
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()

  finally:
    db.session.close()
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  try:
    # Query all venues with search term
    venues = Venue.query.filter(Venue.name.ilike('%'+ request.form.get('search_term') +'%')).all()
    venues_with_attributes = []

    # Find upcoming shows & populate in an array/list
    for venue in venues:
      upcoming_shows = venue.shows.filter(Show.start_time > datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()
      venues_with_attributes.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows)
      })
    # Populate the venues & the count
    response={
      "venues": venues_with_attributes,
      "count": len(venues_with_attributes)
    }
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()

  finally:
    db.session.close()

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  
  try:
    # Query the venue
    venue=Venue.query.filter(Venue.id==venue_id).one()

    # Query & prepare past & upcoming shows
    past_shows=venue.shows.filter(Show.start_time < datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()
    upcoming_shows=venue.shows.filter(Show.start_time > datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()

    data={
      "id": venue.id,
      "name": venue.name,
      "genres": [venue.genres],
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "image_link": venue.image_link,
      "past_shows": [{
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      } for show in past_shows],
      "upcoming_shows": [{
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      }for show in upcoming_shows],
      "past_shows_count": str(len(past_shows)),
      "upcoming_shows_count": str(len(upcoming_shows))
    }
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()

  finally:
    db.session.close()

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  try:
    # The checkbox when unchecked won't exist in request, so needs special handling
    seeking_talent = False

    # Only when the checkbox is checked, "seeking_talent" will be present present in request.form,
    if 'seeking_talent' in request.form:
      seeking_talent = True

    venue = Venue(  
      name=form.name.data,  
      genres=request.form.getlist('genres'),
      address=form.address.data,
      city=form.city.data,
      state= form.state.data,
      phone=form.phone.data,
      website=form.website.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      seeking_talent=seeking_talent,
      seeking_description=request.form['seeking_description']
    )
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()
    flash('An error occurred. Venue ' + form.name.data + 'could not be listed. ')
  finally:
    db.session.close()
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  try:
      # Query all artists with search term
    artists = Artist.query.filter(Artist.name.ilike('%'+ request.form.get('search_term') +'%')).all()
    artists_with_attributes = []

    # Find upcoming shows & populate in a list/array
    for artist in artists:
      upcoming_shows = artist.shows.filter(Show.start_time > datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()
      artists_with_attributes.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": len(upcoming_shows)
      })
    # Populate the artists & the count
    response={
      "artists": artists_with_attributes,
      "count": len(artists_with_attributes)
    }
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()

  finally:
    db.session.close()

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  try:
    # Query the artist
    artist=Artist.query.filter(Artist.id==artist_id).one()
    
    # Query & prepare past & upcoming shows
    past_shows=artist.shows.filter(Show.start_time < datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()
    upcoming_shows=artist.shows.filter(Show.start_time > datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()

    data={
      "id": artist.id,
      "name": artist.name,
      "genres": [artist.genres],
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": [{
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      } for show in past_shows],
      "upcoming_shows": [{
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      }for show in upcoming_shows],
      "past_shows_count": str(len(past_shows)),
      "upcoming_shows_count": str(len(upcoming_shows))
    }
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()

  finally:
    db.session.close()
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form

  form = ArtistForm(request.form)
  # The checkbox when unchecked won't exist in request, so needs special handling
  seeking_venue = False
  # Only when the checkbox is checked, "seeking_talent" will be present present in request.form,
  if 'seeking_venue' in request.form:
    seeking_venue = True

  try:
    artist = Artist(  
      name=form.name.data,  
      genres=request.form.getlist('genres'),
      city=form.city.data,
      state= form.state.data,
      phone=form.phone.data,
      website=form.website.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      seeking_venue=seeking_venue,
      seeking_description=request.form['seeking_description']
    )
    db.session.add(artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + form.name.data + ' was successfully listed!')
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + 'could not be listed. ')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  try:
    shows = Show.query.filter(Show.start_time > datetime.now().strftime('%Y-%m-%d %H:%M:%S')).all()
    data=[]
    for show in shows:
      data.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time)
      })
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()
  finally:
    db.session.close()

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm(request.form)
  try:
    show = Show(  
      artist_id=form.artist_id.data,
      venue_id=form.venue_id.data,
      start_time=form.start_time.data
    )
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except Exception as error:  
    # on unsuccessful db insert, flash an error instead.
    print(str(error))
    db.session.rollback()
    flash('An error occurred. Show could not be listed. ')
  finally:
    db.session.close()

   # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
