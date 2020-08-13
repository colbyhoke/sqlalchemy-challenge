
# ----------------------------------------------
# Colby Alexander Hoke
# UNC Data Analytics Bootcamp, August 2020
# GNU General Public License v3.0
# ----------------------------------------------

################################################
# Set up environment
################################################

import numpy as np
import datetime as dt
from datetime import datetime
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

################################################
# Database setup
################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect existing database into a new model
Base = automap_base()

# reflect tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

################################################
# Flask setup
################################################
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

################################################
# Flask routes
################################################

# ----------------------------------------------
# Home route.
# Lists all available routes.
# ----------------------------------------------

@app.route("/")
def home():
    route_list = []
    route_list.append('Welcome to the API')
    route_list.append('Available routes:')
    route_list.append('/api/v1.0/precipitation')
    route_list.append('/api/v1.0/stations')
    route_list.append('/api/v1.0/stations/names')
    route_list.append('/api/v1.0/stations/ids-and-names')
    route_list.append('/api/v1.0/tobs')
    route_list.append('/api/v1.0/<start>')
    route_list.append('/api/v1.0/<start>/<end>')
    
    routes = list(np.ravel(route_list))
    return jsonify(route_list)
   
# ----------------------------------------------
# /api/v1.0/precipitation
#   Convert the query results to a dictionary using date as the key and prcp as the value.
#   Return the JSON representation of your dictionary.
# ----------------------------------------------
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    results = session.query(Measurement.date, Measurement.prcp).all()
    session.close()

    precip_list = []

    for date, prcp in results:
        precip_dict = {}
        precip_dict[date] = prcp

        precip_list.append(precip_dict)

    return jsonify(precip_list)

# ----------------------------------------------
# /api/v1.0/stations
#   Return a JSON list of stations from the dataset.
#   Homework instructions were unclear on what to return, station id or name, so I have the id here.
# ----------------------------------------------
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    
    # Get all of the station IDs
    results = session.query(Station.station).all()
    session.close()
    
    # Put them into a list
    station_list = list(np.ravel(results))    
    
    # Return the JSON list
    return jsonify(station_list)

# ----------------------------------------------
# /api/v1.0/stations/names
#   Return a JSON list of station names from the dataset.
#   Homework instructions were unclear on what to return, station id or name, so I have the name here.
# ----------------------------------------------
@app.route("/api/v1.0/stations/names")
def stationnames():
    session = Session(engine)
    
    # Get all of the station IDs
    results = session.query(Station.name).all()
    session.close()
    
    # Put them into a list
    station_list = list(np.ravel(results))    
    
    # Return the JSON list
    return jsonify(station_list)

# ----------------------------------------------
# /api/v1.0/stations/names/combined
#   Return a JSON list of station names from the dataset.
#   Homework instructions were unclear on what to return, station id or name, so I have both here.
# ----------------------------------------------
@app.route("/api/v1.0/stations/ids-and-names")
def stationIDnames():
    session = Session(engine)
    
    # Get all of the station IDs
    results = session.query(Station.station, Station.name).all()
    session.close()
    
    # Put them into a list
    station_list = []

    for station, name in results:
        station_dict = {}
        station_dict[station] = name

        station_list.append(station_dict)     
    
    # Return JSON list
    return jsonify(station_list)

# ----------------------------------------------
# /api/v1.0/tobs
#   Query the dates and temperature observations of the most active station for the last year of data.
#   Return a JSON list of temperature observations (TOBS) for the previous year.
# ----------------------------------------------
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)  
    
    # Get the last date recorded
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first() 
    session.close()
    
    # Strip the last date to a datetime object
    date_strip = dt.datetime.strptime(last_date[0], '%Y-%m-%d').date()
    
    # Pull out last year, month, and day
    # Find the date a year before that and save as query_date
    query_date = dt.date(date_strip.year,date_strip.month,date_strip.day) - dt.timedelta(days=365)
    
    # Find the most active station    
    active_station = session.query(Measurement.station, func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()  
    
    # Save the station id
    station_id = active_station[0]
    session.close()
    
    # Now we can use the data from the last year
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == station_id).\
        filter(Measurement.date >= query_date).\
        order_by(Measurement.date).all()
    session.close()

    # Make a list from all of the tobs gethered in the previous query    
    tobs_list = []
    for date, tobs in results:
        tobs_list.append(tobs)

    # Return JSON list
    return jsonify(tobs_list)

# ----------------------------------------------
# /api/v1.0/<start> and /api/v1.0/<start>/<end>
#   Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start.
#   Calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
# ----------------------------------------------
@app.route("/api/v1.0/<start>")
def start(start):
    session = Session(engine)
    
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()

    # Catch incorrectly formatted dates
    except ValueError:
        return "Please format your date as YYYY-MM-DD"
    
    # Format the provided date to use in queries
    query_start = f'{start_date.year}-{start_date.month:02d}-{start_date.day:02d}'

    # Get max, min, and avg for dates equal to and later than provided date
    temp_max = session.query(func.max(Measurement.tobs)).\
                filter(Measurement.date >= query_start).first()
    temp_min = session.query(func.min(Measurement.tobs)).\
                filter(Measurement.date >= query_start).first()
    temp_avg = session.query(func.avg(Measurement.tobs)).\
                filter(Measurement.date >= query_start).first()
    session.close()

    # Since the queries returned were lists (of 1 item), we only need the first values
    results = [temp_min[0], round(temp_avg[0],2), temp_max[0]]

    # Return JSON list
    return jsonify(results)

# ----------------------------------------------
# /api/v1.0/<start> and /api/v1.0/<start>/<end>
#   Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start-end range.
#   Calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.
# ----------------------------------------------
@app.route("/api/v1.0/<start>/<end>")
def startend(start, end):
    session = Session(engine)
    
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    
    # Catch incorrectly formatted dates
    except ValueError:
        return "Error: Please format your dates as YYYY-MM-DD"
    
    # Format the provided dates to use in queries
    query_start = f'{start_date.year}-{start_date.month:02d}-{start_date.day:02d}'
    query_end = f'{end_date.year}-{end_date.month:02d}-{end_date.day:02d}'

    # Get max, min, and avg for dates in provided range
    try:
        temp_max = session.query(func.max(Measurement.tobs)).\
            filter(Measurement.date >= query_start, Measurement.date <= query_end).first()
        temp_min = session.query(func.min(Measurement.tobs)).\
            filter(Measurement.date >= query_start, Measurement.date <= query_end).first()
        temp_avg = session.query(func.avg(Measurement.tobs)).\
            filter(Measurement.date >= query_start, Measurement.date <= query_end).first()
        session.close()
        
        # Since the queries returned were lists (of 1 item), we only need the first values
        results = [temp_min[0], round(temp_avg[0],2), temp_max[0]]
    
    # Catch end dates that are before start dates
    except TypeError:
        return "Error: End date must be after start date."
    
    # Return JSON list
    return jsonify(results)

# ----------------------------------------------
# Run directly
# ----------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)