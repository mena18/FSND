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
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import literal,func,or_
from datetime import datetime
from sqlalchemy.sql import label,case

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app,db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#




class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    address = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    image_link = db.Column(db.String(500),nullable=False)
    facebook_link = db.Column(db.String(120),nullable=False)
    

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    # artists = db.relationship('Artist',secondary = "shows",backref="venues")
    genres = db.Column(db.String(120),nullable=False)
    seeking_talent = db.Column(db.Boolean,default=False)
    seeking_description =  db.Column(db.String(500),default="")
    show = db.relationship("Show",cascade="all, delete-orphan")

    


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    genres = db.Column(db.String(120),nullable=False)
    image_link = db.Column(db.String(500),nullable=False)
    facebook_link = db.Column(db.String(120),nullable=False)


    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    # venues = db.relationship('Venue',secondary = "show")
    seeking_venue = db.Column(db.Boolean,default=False)
    seeking_description =  db.Column(db.String(500),default="")
    show = db.relationship("Show",cascade="all, delete-orphan")

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


# i made the show as class extends db.model because i have extra field 'date' to add with the 2 foreignkeys'  

#-------------
# Update (Review-1)
#--------------
# - change table names to be plural 
# - change the cascade="all, delete-orphan" to be in the main class (Artist,venue) not the intermediate (Show) which fix 
#   the problem of deletion 
# - remove the relationship from venue to artist and this make me now unable to write artist.venues.append(venue) but i wouldn't write 
#   this any way because every relationship between venue and artist need 'date' field so it's easier to add them by creaing
#   show instance  (i know removing this relationship  seems as if i am just not using many to many relationship at all)
#   but i am using it i just made the refrence from the show to (Artist,venue) and from (Artist,venue) to the show so know i have 2 tables and a third one
#   that have 2 foreign keys pointing to them (which is exactly the many to many relationship ) just with custom implementation
#   to allow me to add 'date' field , and allow relationship between the same artist and venue with different dates with no      
#   error on deletion .
#   i get the idea from https://stackoverflow.com/questions/7417906/sqlalchemy-manytomany-secondary-table-with-additional-fields
#----------------


class Show(db.Model):  # show represent the show (many to many relationship between venus and artists)
    __tablename__ = "shows"

    id = db.Column(db.Integer,primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id') )
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))
    date = db.Column(db.DateTime,default=datetime.utcnow())

    venue = db.relationship(Venue)
    artist = db.relationship(Artist)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  # date = dateutil.parser.parse(value)
  # i removed the previous line because value type is already datetime  
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(value, format)

app.jinja_env.filters['datetime'] = format_datetime
# SELECT venue.id AS venue_id, count(show.id) AS count_1 FROM venue JOIN show ON venue.id = show.venue_id GROUP BY venue.id
# SELECT venue.name AS venue_name, count(show.id) AS count_1 FROM venue JOIN show ON venue.id = show.venue_id GROUP BY venue.name
# ans = db.session.query(Venue, label("counter",func.count(Show.id))).join(Show,Show.venue_id==Venue.id).group_by(Venue).order_by('city').all()
# SELECT venue.name AS venue_name, count(show.id) AS counter FROM venue JOIN show ON show.venue_id = venue.id GROUP BY venue.name
# ans = db.session.query(Venue, label("counter",func.count(Show.id))).outerjoin(Show,Show.venue_id==Venue.id).group_by(Venue).order_by('city').all()


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
  artists = db.session.query(Artist).order_by(Artist.id.desc()).limit(10).all();
  venues = db.session.query(Venue).order_by(Venue.id.desc()).limit(10).all();    
  return render_template('pages/home.html',venues=venues,artists=artists)



# Venues
#  -----------------------------------------------------------------

@app.route('/venues')
def venues():


  # TODO: replace with real venues data.
  # num_shows should be aggregated based on number of upcoming shows per venue.

  
  data = []
  
  # getting all the venues with number of upcoming shows in one query
  venues = db.session.query(Venue, label("counter",func.count(case([(Show.date > datetime.now(), 1)],else_=None)))).outerjoin(Show,Show.venue_id==Venue.id).group_by(Venue).order_by('city').all()


  # grouping all the venues by the city 
  for venue,counter in venues:
    if (len(data)>0 and venue.city == data[-1]['city']):
      data[-1]['venues'].append({
        'id':venue.id,
        'name':venue.name,
        'num_upcoming_shows':counter,
      })
    else:
      data.append({'city':venue.city,
      'state':venue.state,
      'venues':[{
         'id':venue.id,
        'name':venue.name,
        'num_upcoming_shows':counter,
      }],
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  #-------------
  # Update (Review-1)
  #--------------
  # using ilike in the search instead of converting  them to lower
  #----------------


  search_for = request.form.get('search_term', '')



  # matching with names,city,
  match_all = Venue.query.filter( 
    or_(
      Venue.name.ilike(f'%{search_for}%'), # f'{val}' == '{}'.format(val)
      or_(
        Venue.city.ilike(f'%{search_for}%'),
        Venue.state.ilike(f'%{search_for}%'))
       ) ).all()
    
  count = len(match_all)

  response = {'count':count,"data":match_all}
  return render_template('pages/search_venues.html', results=response, search_term=search_for)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  #-------------
  # Update (Review-1)
  #--------------
  # using join between shows and Artist insted of artist.shows
  #----------------

  data = Venue.query.get_or_404(venue_id);
  data.upcoming_shows = [];
  data.past_shows = [];

  shows = db.session.query(
    label("artist_id",Artist.id),
    label("artist_name",Artist.name),
    label("artist_image_link",Artist.image_link),
    label("start_time",Show.date),
    label("venue_id",Show.venue_id),
    ).select_from(Show).filter_by(venue_id=venue_id).join(Artist).all()

  # i get  all the shows and seperate them in python instead of making 2 quiries one to get the previous shows and one
  # to get the upcoming 
  for show in shows:
    if(show.start_time > datetime.now()):
      data.upcoming_shows.append(show)
    else:
      data.past_shows.append(show)
  data.upcoming_shows_count = len(data.upcoming_shows);
  data.past_shows_count = len(data.past_shows);


  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form,status="create")


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


  form = VenueForm()

  if form.validate_on_submit():
    
    venue = Venue()
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.genres = ",".join(form.genres.data) # genres stored as string but should be sent as list
    venue.seeking_description = form.seeking_description.data
    venue.seeking_talent = form.seeking_talent.data

    db.session.add(venue)
    db.session.commit()

    flash('Venue ' + form.name.data + ' was successfully listed!')
    
    return redirect(url_for('show_venue', venue_id=venue.id))
  else:
    return render_template('forms/new_venue.html', form=form,status="create")

  return redirect(url_for('index'))



#  Update Venue
#  ----------------------------------------------------------------


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  # TODO: populate form with values from venue with ID <venue_id>

  form = VenueForm()
  venue = Venue.query.get_or_404(venue_id);
  if(venue.genres):
    venue.genres = venue.genres.split(",");
  # passing the objecr value directly to the form and sending the form itself with the previous data
  form = VenueForm(obj = venue)

  return render_template('forms/new_venue.html', form=form ,status="update")

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  form = VenueForm()
  venue = Venue.query.get_or_404(venue_id)
  if form.validate_on_submit():
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.genres = ",".join(form.genres.data)
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    db.session.add(venue)
    db.session.commit()

    flash('Venue ' + form.name.data + ' was successfully updated!')
    
    return render_template('pages/show_venue.html',venue=venue)
  else:
    return render_template('forms/new_venue.html', form=form,status="update")



  return redirect(url_for('show_venue', venue_id=venue_id))



#  Delete Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  
  
  #-------------
  # Update (Review-1)
  #--------------
  # change delete function
  #----------------
  
  try:

    venue = Venue.query.get_or_404(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash("deleted successfully");

  except :
    flash("Error happen")

  return redirect(url_for('index'))



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  data = db.session.query(Artist.id,Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  #-------------
  # Update (Review-1)
  #--------------
  # using ilike in the search instead of converting  them to lower
  #----------------

  search_for = request.form.get('search_term', '')

  # matching with names,city,
  match_all = Artist.query.filter( 
    or_(
      Artist.name.ilike(f'%{search_for}%'),
      or_(
        Artist.city.ilike(f'%{search_for}%'),
        Artist.state.ilike(f'%{search_for}%'))
       ) ).all()
    
  count = len(match_all)
  
  response = {'count':count,"data":match_all}
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))



@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  

  #-------------
  # Update (Review-1)
  #--------------
  # using join between shows and Venues insted of venue.shows
  #----------------

  data = Artist.query.get_or_404(artist_id);
  data.upcoming_shows = [];
  data.past_shows = [];
  shows =   db.session.query(
    label("venue_id",Venue.id),
    label("venue_name",Venue.name),
    label("venue_image_link",Venue.image_link),
    label("start_time",Show.date),
    label("artist_id",Show.artist_id),
    ).select_from(Show).filter_by(artist_id=artist_id).join(Venue).all()

  for show in shows:
    if(show.start_time > datetime.now()):
      data.upcoming_shows.append(show)
    else:
      data.past_shows.append(show)
  data.upcoming_shows_count = len(data.upcoming_shows);
  data.past_shows_count = len(data.past_shows);
  
  
  return render_template('pages/show_artist.html', artist=data)




#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form,status="create")


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion


  form = ArtistForm()
  if (form.validate_on_submit()):
    artist = Artist()
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.genres = ",".join(form.genres.data)
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data

    db.session.add(artist)
    db.session.commit()

    flash('Artist ' + form.name.data + ' was successfully listed!')
    return redirect(url_for('show_artist', artist_id=artist.id))
  else:
    return render_template('forms/new_artist.html', form=form, status="create")




#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # TODO: populate form with fields from artist with ID <artist_id>

  artist = Artist.query.get_or_404(artist_id);
  if(artist.genres):
    artist.genres = artist.genres.split(",");
  # passing the objecr value directly to the form and sending the form itself with the previous data
  form = ArtistForm(obj = artist)

  return render_template('forms/new_artist.html', form=form, status="update")

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes


  form = ArtistForm()
  artist = Artist.query.get_or_404(artist_id)
  if (form.validate_on_submit()):
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.genres = ",".join(form.genres.data)
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
   
    db.session.add(artist)
    db.session.commit()

    flash("done")
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    return render_template('forms/new_artist.html', form=form, status="update")


  



# Delete artists
#  ----------------------------------------------------------------

@app.route('/artists/<artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
  
  #-------------
  # Update (Review-1)
  #--------------
  # change delete function
  #----------------

  try:
    artist = Artist.query.get_or_404(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash("deleted successfully");
  except :
    flash("Error happen")

  return redirect(url_for('index'))




#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  

  data = db.session.query(
    label("venue_id",Venue.id),
    label("venue_name",Venue.name),
    label("artist_id",Artist.id),
    label("artist_name",Artist.name),
    label("artist_image_link",Artist.image_link),
    label("start_time",Show.date)
  ).select_from(Show).join(Artist).join(Venue).all()


  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create',methods=['GET'])
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  form = ShowForm()
  
  if (form.validate_on_submit()):
    try:
        
      show = Show()
      show.venue_id = form.venue_id.data
      show.artist_id = form.artist_id.data
      show.date = form.start_time.data
      
      db.session.add(show)
      db.session.commit()

      flash("created successfully")
      return redirect(url_for('index'))
    except :
      flash("The id of artist or venue is wrong ");
      return render_template('forms/new_show.html', form=form)

  else:
    return render_template('forms/new_show.html', form=form)


  

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
    # port = int(os.environ.get('PORT', 5000))
    app.run( port='5000')
'''