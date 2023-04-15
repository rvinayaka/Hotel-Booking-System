from flask import Flask, request, jsonify
from conn import connection
from settings import logger, handle_exceptions
import psycopg2

app = Flask(__name__)


# Question:
# Design a class to manage hotel bookings,
# including room availability, reservations, and cancellations.


# Query:
# CREATE room_id details AS (name VARCHAR (100), mobile_no INTEGER, city VARCHAR (100));

# CREATE TABLE hotel(id SERIAL PRIMARY KEY, guest_details details, checkin DATE NOT NULL,
# checkout DATE NOT NULL, status VARCHAR(300));


# Hotel Table:
#  id |          guest_details           | room_id |  checkin   |  checkout  | status
# ----+----------------------------------+---------+------------+------------+--------
#   1 | (Naruto,5552304,"LEAF village")  |     101 | 2023-04-05 | 2023-04-10 | booked
#   3 | (Chiraku,2224123,"Sand Village") |     102 | 2022-08-15 | 2022-09-19 | booked
#   2 | (Hinata,9004114,"Water Village") |     102 | 2022-09-12 | 2022-12-09 | booked

# Rooms table
#  room_id | guest_id | room_type |       status
# ---------+----------+-----------+---------------------
#      101 |        1 | 3BHK      | cleaned
#      102 |        2 | 1BHK      | uncleaned
#      103 |        3 | double    | cleaning inprogress


@app.route('/guests', methods=["POST"], endpoint='add_new_guests')
@handle_exceptions
def add_new_guests():           # adding new people who have taken the things from hotel
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to add guests in the list")

    guest_details = request.json["details"]
    room_id = request.json["roomId"]
    checkin = request.json["checkin"]
    checkout = request.json["checkout"]
    status = request.json["status"]

    # input_format:{
    #     "details": {
    #         "name": "Chiraku",
    #         "mobile_no": 2224123,
    #         "city": "Sand Village"
    #     },
    #     "roomId": 102,
    #     "checkin": "2022-08-15",
    #     "checkout": "2022-09-19",
    #     "status": "booked"
    # }

    print(guest_details, room_id, checkin, checkout, status)

    add_query = """INSERT INTO hotel(guest_details, room_id, checkin, checkout, 
                        status)VALUES(ROW(%s, %s, %s)::details, %s, %s::date, %s::date, %s);"""

    values = (guest_details["name"], guest_details["mobile_no"], guest_details["city"], room_id,
              checkin, checkout, status)
    cur.execute(add_query, values)
    # commit to database
    conn.commit()
    logger(__name__).info(f"{guest_details['name']} added in the list")
    return jsonify({"message": f"{guest_details['name']} added in the list"}), 200


@app.route('/rooms', methods=["POST"], endpoint='add_room_details')
@handle_exceptions
def add_room_details():           # adding room_id and guest_id
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to add guests in room_id in the rooms table")

    # Get values from the user
    data = request.get_json()
    room_id = data.get('room_id')
    guest_id = data.get('guest_id')
    room_type = data.get('room_type')
    status = data.get('status')
    print(room_id, guest_id, room_type, status)

    add_query = """INSERT INTO rooms(room_id, guest_id, room_type, status)VALUES(%s, %s, %s, %s);"""
    values = (room_id, guest_id, room_type, status)

    # Execute the query
    cur.execute(add_query, values)

    # commit to database
    conn.commit()

    # Log the details in the log file
    logger(__name__).info(f"Guest with id {guest_id} has been shifted to room id {room_id}")
    return jsonify({"message": f"Guest with id {guest_id} has been shifted to room id {room_id}",
                    "Details": data}), 200


@app.route("/show_entries", methods=["GET"], endpoint='show_entries')            # READ all entries
@handle_exceptions
def show_entries():
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display all guests in the list")

    show_query = "SELECT * FROM hotel;"
    cur.execute(show_query)
    data = cur.fetchall()
    # Log the details into logger file
    logger(__name__).info("Displayed list of all guests in the list")

    return jsonify({"message": data}), 200



@app.route("/status/<int:sno>", methods=["PUT"], endpoint='booking_status')            # Get booking status of all rooms
@handle_exceptions
def booking_status(sno):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update booking status of rooms in the list")

    status = request.json["status"]
    update_query = "UPDATE hotel SET status = %s WHERE room_id = %s"

    cur.execute(update_query, (status, sno))

    # Log the details into logger file
    logger(__name__).info(f"Status updated of room no. {sno}")
    return jsonify({"message": f"Status updated of room no. {sno}"}), 200


@app.route("/search/<string:status>", methods=["GET"], endpoint='search_booking_status')            # Search guests in the list
@handle_exceptions
def search_booking_status(status):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display all guests in the list")

    show_query = "SELECT guest_details, status FROM hotel WHERE status = %s;"

    cur.execute(show_query, (status,))
    data = cur.fetchall()
    # Log the details into logger file
    logger(__name__).info("Displayed list of all guests in the list")

    return jsonify({"message": data}), 200


@app.route("/guests/<int:id>", methods=["PUT"], endpoint='update_guest_details')
@handle_exceptions
def update_guest_details(id):                  # Update the details
    # Starting database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update the details ")

    # Check room present in the table
    cur.execute("SELECT room_id from hotel where id = %s", (id,))
    get_room_id = cur.fetchone()

    # If room not present return message
    if not get_room_id:
        return jsonify({"message": "Details not found"}), 200

    data = request.get_json()
    guest_details = data.get('details')
    checkin = data.get('checkin')
    checkout = data.get('checkout')
    status = data.get('status')

    # Check what details has to be updated
    if guest_details:
        cur.execute("UPDATE hotel SET guest_details = ROW(%s, %s, %s)::details WHERE id = %s",
                    (guest_details['name'], guest_details['mobile_no'], guest_details['city'], id))
    elif checkin:
        cur.execute("UPDATE hotel SET checkin = %s WHERE id = %s", (checkin, id))
    elif checkout:
        cur.execute("UPDATE hotel SET checkout = %s WHERE id = %s", (checkout, id))
    elif status:
        cur.execute("UPDATE hotel SET status = %s WHERE id = %s", (status, id))

    # Commit the changes into the table
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Details updated: {data}")
    return jsonify({"message": "Details updated", "Details": data}), 200

@app.route("/delete/<int:id>", methods=["DELETE"], endpoint='delete_guests')      # DELETE guests from the table
@handle_exceptions
def delete_guests(id):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to delete the patients from the table")

    # Execute the query
    delete_query = "DELETE from hotel WHERE id = %s"
    cur.execute(delete_query, (id,))
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Account no {id} deleted from the table")
    return jsonify({"message": "Deleted Successfully", "item_no": id}), 200


@app.route("/checkout/<int:id>", methods=["GET"], endpoint='generate_bill_to_checkout')
@handle_exceptions
def generate_bill_to_checkout(id):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to generate bill of guests")

    # get query
    show_query = "SELECT * FROM hotel WHERE id = %s;"
    # Execute the query
    cur.execute(show_query, id)
    data = cur.fetchall()

    # Log the details into logger file
    logger(__name__).info(f"Bill generated of guests with id no.{id} in the list")
    return jsonify({"message": f"Bill generated of guests with id no.{id} in the list",
                    "Details": data}), 200


@app.route("/rooms/<int:room_id>", methods=["PUT"], endpoint='update_room_details')
@handle_exceptions
def update_room_details(room_id):                  # Update the details
    # Starting database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update the details ")

    cur.execute("SELECT * from rooms where room_id = %s", (room_id,))
    get_rooms = cur.fetchone()

    if not get_rooms:
        return jsonify({"message": "Details not found"}), 200

    # Get values from the user
    data = request.get_json()
    guest_id = data.get('guest_id')
    room_type = data.get('room_type')
    status = data.get('status')

    print(room_id, guest_id, room_type, status)

    # if guest_id:
    #     cur.execute("UPDATE rooms SET guest_id = %s WHERE room_id = %s", (guest_id, room_id))
    # if status:
    #     cur.execute("UPDATE rooms SET status = %s WHERE room_id = %s", (status, room_id))
    # elif room_type:
    #     cur.execute("UPDATE rooms SET room_type = %s WHERE room_id = %s", (room_type, room_id))

    if guest_id:
        cur.execute("UPDATE rooms SET guest_id = %s WHERE room_id = %s", (guest_id, room_id))
    if status:
        cur.execute("UPDATE rooms SET status = %s WHERE room_id = %s", (status, room_id))
    if room_type:
        cur.execute("UPDATE rooms SET room_type = %s WHERE room_id = %s", (room_type, room_id))

    # Commit the change into the table
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Details updated: {data}")
    return jsonify({"message": "Details updated", "Details": data}), 200


@app.route("/show_rooms", methods=["GET"], endpoint='show_all_rooms')
@handle_exceptions
def show_all_rooms():
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display all guests in the list")

    show_query = "SELECT * FROM rooms;"
    cur.execute(show_query)
    data = cur.fetchall()

    # Log the details into logger file
    logger(__name__).info("Displayed list of all guests in the list")
    return jsonify({"message": data}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)



