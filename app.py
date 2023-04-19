from flask import Flask, request, jsonify
from settings import connection, logger, handle_exceptions

app = Flask(__name__)


# Question:
# Design a class to manage hotel bookings,
# including room availability, reservations, and cancellations.


# Query:
# CREATE room_id details AS (name VARCHAR (100), mobile_no INTEGER, city VARCHAR (100));

# CREATE TABLE hotel(id SERIAL PRIMARY KEY, guest_details details, checkin DATE NOT NULL,
# checkout DATE NOT NULL, payment_status VARCHAR(300));


# Hotel Table:
#  id |          guest_details           | room_id |  checkin   |  checkout  | payment_status
# ----+----------------------------------+---------+------------+------------+----------------
#   1 | (Naruto,5552304,"LEAF village")  |     101 | 2023-04-05 | 2023-04-10 | done
#   2 | (Hinata,9004114,"Water Village") |     102 | 2022-09-12 | 2022-12-09 | pending
#   3 | (Chiraku,2224123,"Sand Village") |     103 | 2022-08-15 | 2022-09-19 | done
#   4 | (Gaara,221109884,"Sand Village") |     104 | 2021-06-03 | 2021-08-10 | pending


# Rooms table
#  room_id | guest_id | room_type |     room_status     | booking_status
# ---------+----------+-----------+---------------------+----------------
#      102 |        2 | 1BHK      | uncleaned           | booked
#      104 |        4 | 1RK       | uncleaned           | unbooked
#      103 |        3 | 3BHK      | cleaning inprogress | booked
#      101 |        1 | 2BHK      | cleaning            | booked



"""Admin API"""
@app.route('/guests', methods=["POST"], endpoint='add_new_guests')
@handle_exceptions
def add_new_guests():  # adding new people who have taken the things from hotel
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to add guests in the list")

    # Getting values from the user
    # since guest_details is the json value taking values in the details dictionary format
    guest_details = request.json["details"]
    room_id = request.json["roomId"]
    checkin = request.json["checkin"]
    checkout = request.json["checkout"]
    payment_status = request.json["payment_status"]

    # input_format:{
    #     "details": {
    #         "name": "Chiraku",
    #         "mobile_no": 2224123,
    #         "city": "Sand Village"
    #     },
    #     "roomId": 102,
    #     "checkin": "2022-08-15",
    #     "checkout": "2022-09-19",
    #     "payment_status": "booked"
    # }

    print(guest_details, room_id, checkin, checkout, payment_status)

    # Add query
    add_query = """INSERT INTO hotel(guest_details, room_id, checkin, checkout, 
                        payment_status)VALUES(ROW(%s, %s, %s)::details, %s, %s::date, %s::date, %s);"""

    values = (guest_details["name"], guest_details["mobile_no"], guest_details["city"], room_id,
              checkin, checkout, payment_status)
    # Execute the query
    cur.execute(add_query, values)

    # commit to database
    conn.commit()
    # Log the values in log file
    logger(__name__).info(f"{guest_details['name']} added in the list")

    # close the database connection
    logger(__name__).warning("Hence item added, closing the connection")
    return jsonify({"message": f"{guest_details['name']} added in the list"}), 200


"""Admin API"""
@app.route('/rooms', methods=["POST"], endpoint='add_room_details')
@handle_exceptions
def add_room_details():  # adding room_id and guest_id
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to add guests in room_id in the rooms table")

    # Get values from the user
    data = request.get_json()
    room_id = data.get('room_id')
    guest_id = data.get('guest_id')
    room_type = data.get('room_type')
    room_status = data.get('room_status')
    booking_status = data.get('booking_status')

    print(room_id, guest_id, room_type, booking_status)

    add_query = """INSERT INTO rooms(room_id, guest_id, room_type, room_status, booking_status)VALUES(%s, %s, %s, %s, %s);"""
    values = (room_id, guest_id, room_type, room_status, booking_status)

    # Execute the query
    cur.execute(add_query, values)

    # commit to database
    conn.commit()

    # Log the details in the log file
    logger(__name__).info(f"Guest with id {guest_id} has been shifted to room id {room_id}")

    # close the database connection
    logger(__name__).warning("Hence room details added, closing the connection")
    return jsonify({"message": f"Guest with id {guest_id} has been shifted to room id {room_id}",
                    "Details": data}), 200


"""Functional API"""
# To view all the detailed entries of guests in hotel
@app.route('/', methods=["GET"], endpoint="show_entries")
@handle_exceptions
def show_entries():
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display all guests in the list")

    # To show all the details of both the table
    show_all_query = "SELECT * " \
                     "FROM hotel JOIN rooms ON hotel.room_id = rooms.room_id " \
                     "WHERE hotel.room_id = rooms.room_id;"

    """To show roomId, guestDetails, roomStatus, bookingStatus"""
    # show_query = "SELECT rooms.room_id, hotel.guest_details, " \
    #              "rooms.room_status, rooms.booking_status " \
    #              "FROM hotel JOIN rooms ON hotel.room_id = rooms.room_id " \
    #              "WHERE hotel.room_id = rooms.room_id;"

    cur.execute(show_all_query)
    data = cur.fetchall()
    # Log the details into logger file
    logger(__name__).info("Displayed list of all guests and rooms with details in the list")

    # close the database connection
    logger(__name__).warning("Hence list showed, closing the connection")
    logger(__name__).warning("Hence list showed, closing the connection")
    return jsonify({"message": "Displayed list of all guests and rooms with details in the list",
                    "details": data}), 200


"""Admin API"""
# UPDATE payment status of a particular room
@app.route("/payment_status/<int:sno>", methods=["PUT"], endpoint='update_payment_status')
@handle_exceptions
def update_payment_status(sno):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update payment status of room in the list")

    # Check room present in the table
    cur.execute("SELECT * from hotel where room_id = %s", (sno,))
    get_room_id = cur.fetchone()

    # If room not present return message
    if not get_room_id:
        return jsonify({"message": f"Room with id {sno} not found, try again"}), 200

    payment_status = request.json["payment_status"]
    update_query = "UPDATE hotel SET payment_status = %s WHERE room_id = %s"

    cur.execute(update_query, (payment_status, sno))

    # Commit the changes to table
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Payment Status of room no. {sno}, updated to {payment_status}")

    # close the database connection
    logger(__name__).warning("Hence status updated, closing the connection")
    return jsonify({"message": f"Payment Status of room no. {sno}, updated to {payment_status}"}), 200


"""Functional API"""
@app.route("/search/<string:payment_status>", methods=["GET"], endpoint='search_booking_status')  # Search guests in the list
@handle_exceptions
def check_payment_status(payment_status):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display all payment_status of all guests in the list")

    show_query = "SELECT guest_details, payment_status FROM hotel WHERE payment_status = %s;"

    cur.execute(show_query, (payment_status,))
    data = cur.fetchall()

    # Log the details into logger file
    logger(__name__).info(f"Displayed list of all guests whose payment status is {payment_status} in the list")

    # close the database connection
    logger(__name__).warning("Hence status checked, closing the connection")
    return jsonify({"message": f"Displayed list of all guests whose payment status is {payment_status} in the list",
                    "details": data}), 200


"""Admin API"""
@app.route("/guests/<int:id>", methods=["PUT"], endpoint='update_guest_details')
@handle_exceptions
def update_guest_details(id):  # Update the details
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
    payment_status = data.get('payment_status')

    # Check what details has to be updated
    if guest_details:
        cur.execute("UPDATE hotel SET guest_details = ROW(%s, %s, %s)::details WHERE id = %s",
                    (guest_details['name'], guest_details['mobile_no'], guest_details['city'], id))
    elif checkin:
        cur.execute("UPDATE hotel SET checkin = %s WHERE id = %s", (checkin, id))
    elif checkout:
        cur.execute("UPDATE hotel SET checkout = %s WHERE id = %s", (checkout, id))
    elif payment_status:
        cur.execute("UPDATE hotel SET payment_status = %s WHERE id = %s", (payment_status, id))

    # Commit the changes into the table
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Details updated: {data}")

    # close the database connection
    logger(__name__).warning("Hence details updated, closing the connection")
    return jsonify({"message": "Details updated", "Details": data}), 200


"""Admin API"""
@app.route("/delete/<int:id>", methods=["DELETE"], endpoint='delete_guests')  # DELETE guests from the table
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

    # close the database connection
    logger(__name__).warning("Hence guests deleted, closing the connection")
    return jsonify({"message": "Deleted Successfully", "item_no": id}), 200


"""Functional API"""
@app.route("/checkout/<int:id>", methods=["GET"], endpoint='generate_bill_to_checkout')
@handle_exceptions
def generate_bill_to_checkout(id):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to generate bill of guests")

    # get query
    show_query = "SELECT * FROM hotel WHERE id = %s;"

    show_query = "SELECT " \
                 "rooms.room_id, hotel.guest_details, rooms.room_type, " \
                 "hotel.checkin, hotel.checkout, hotel.payment_status " \
                 "FROM hotel JOIN rooms ON hotel.room_id = rooms.room_id " \
                 "WHERE hotel.room_id = rooms.room_id;"
    # Execute the query
    cur.execute(show_query, id)
    data = cur.fetchall()

    # Log the details into logger file
    logger(__name__).info(f"Bill generated of guests with id no.{id} in the list")

    # close the database connection
    logger(__name__).warning("Hence bill generated, closing the connection")
    return jsonify({"message": f"Bill generated of guests with id no.{id} in the list",
                    "Details": data}), 200


"""Admin API"""
@app.route("/rooms/<int:room_id>", methods=["PUT"], endpoint='update_room_details')
@handle_exceptions
def update_room_details(room_id):  # Update the details
    # Starting database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update the details ")

    cur.execute("SELECT * from rooms where room_id = %s", (room_id,))
    get_rooms = cur.fetchone()

    # Return message if room not found
    if not get_rooms:
        return jsonify({"message": f"Room of id no.{room_id} not found, try again"}), 200

    # Get values from the user
    data = request.get_json()
    guest_id = data.get('guest_id')
    room_type = data.get('room_type')
    room_status = data.get('room_status')
    booking_status = data.get('booking_status')

    print(room_id, guest_id, room_type, booking_status)

    # Check what details has been provided by user and then update
    if guest_id:
        cur.execute("UPDATE rooms SET guest_id = %s WHERE room_id = %s", (guest_id, room_id))
    if room_status:
        cur.execute("UPDATE rooms SET room_status = %s WHERE room_id = %s", (room_status, room_id))
    if booking_status:
        cur.execute("UPDATE rooms SET booking_status = %s WHERE room_id = %s", (booking_status, room_id))
    if room_type:
        cur.execute("UPDATE rooms SET room_type = %s WHERE room_id = %s", (room_type, room_id))

    # Commit the change into the table
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Details updated: {data}")

    # close the database connection
    logger(__name__).warning("Hence room details updated, closing the connection")
    return jsonify({"message": "Details updated", "Details": data}), 200


"""Functional API"""
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

    # close the database connection
    logger(__name__).warning("Hence all rooms showed, closing the connection")
    return jsonify({"message": data}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
