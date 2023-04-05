from flask import Flask, request, jsonify
from conn import connection
from settings import logger
import psycopg2

app = Flask(__name__)


# Question:
# Design a class to manage hotel bookings,
# including room availability, reservations, and cancellations.


# Query:
# CREATE room_id details AS (name VARCHAR (100), mobile_no INTEGER, city VARCHAR (100));

# CREATE TABLE hotel(id SERIAL PRIMARY KEY, guest_details details, checkin DATE NOT NULL,
# checkout DATE NOT NULL, status VARCHAR(300));


# Table:
#  id |          guest_details           | room_id |  checkin   |  checkout  | status
# ----+----------------------------------+---------+------------+------------+--------
#   1 | (Naruto,5552304,"LEAF village")  |     101 | 2023-04-05 | 2023-04-10 | booked
#   3 | (Chiraku,2224123,"Sand Village") |     102 | 2022-08-15 | 2022-09-19 | booked
#   2 | (Hinata,9004114,"Water Village") |     102 | 2022-09-12 | 2022-12-09 | booked


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except psycopg2.Error as error:
            conn = kwargs.get('conn')
            if conn:
                conn.rollback()
            logger(__name__).error(f"Error occurred: {error}")
            return jsonify({"message": f"Error occurred: {error}"})
        except Exception as error:
            logger(__name__).error(f"Error occurred: {error}")
            return jsonify({"message": f"Error occurred: {error}"})
        finally:
            conn = kwargs.get("conn")
            cur = kwargs.get("cur")
            # close the database connection
            if conn:
                conn.close()
            if cur:
                cur.close()
            logger(__name__).warning("Closing the connection")
    return wrapper



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


@app.route("/", methods=["GET"], endpoint='show_entries')            # READ the cart list
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



@app.route("/status/<int:sno>", methods=["PUT"], endpoint='booking_status')            # READ the cart list
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


@app.route("/search/<string:name>", methods=["GET"], endpoint='search_booking_status')            # READ the cart list
@handle_exceptions
def search_booking_status(name):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to display all guests in the list")
    print("name type", type(name))

    show_query = "SELECT * FROM hotel WHERE status = %s;"

    cur.execute(show_query, (name,))
    data = cur.fetchall()
    # Log the details into logger file
    logger(__name__).info("Displayed list of all guests in the list")

    return jsonify({"message": data}), 200


@app.route("/rooms/<int:id>", methods=["PUT"], endpoint='update_guest_details')
@handle_exceptions
def update_guest_details(id):                  # Update the details
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to update the details ")

    cur.execute("SELECT room_id from hotel where id = %s", (id,))
    get_room_id = cur.fetchone()

    if not get_room_id:
        return jsonify({"message": "Details not found"}), 200

    data = request.get_json()
    guest_details = data.get('details')
    checkin = data.get('checkin')
    checkout = data.get('checkout')
    status = data.get('status')

    if guest_details:
        cur.execute("UPDATE hotel SET guest_details = ROW(%s, %s, %s)::details WHERE id = %s",
                    (guest_details['name'], guest_details['mobile_no'], guest_details['city'], id))
    elif checkin:
        cur.execute("UPDATE hotel SET checkin = %s WHERE id = %s", (checkin, id))
    elif checkout:
        cur.execute("UPDATE hotel SET checkout = %s WHERE id = %s", (checkout, id))
    elif status:
        cur.execute("UPDATE hotel SET status = %s WHERE id = %s", (status, id))

    conn.commit()
    # Log the details into logger file
    logger(__name__).info(f"Details updated: {data}")
    return jsonify({"message": "Details updated", "Details": data}), 200

@app.route("/delete/<int:id>", methods=["DELETE"], endpoint='delete_guests')      # DELETE an item from cart
@handle_exceptions
def delete_guests(id):
    # start the database connection
    cur, conn = connection()
    logger(__name__).warning("Starting the db connection to delete the patients from the table")

    delete_query = "DELETE from hotel WHERE id = %s"
    cur.execute(delete_query, (id,))
    conn.commit()

    # Log the details into logger file
    logger(__name__).info(f"Account no {id} deleted from the table")
    return jsonify({"message": "Deleted Successfully", "item_no": id}), 200




if __name__ == "__main__":
    app.run(debug=True, port=5000)



