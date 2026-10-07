from fastapi import FastAPI
from database import get_connection
from datetime import datetime

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Smart Parking Management System is running"
    }


@app.get("/slots")
def get_slots():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM parking_slots")

    slots = cursor.fetchall()

    cursor.close()
    connection.close()

    return slots




@app.post("/entry")
def vehicle_entry(vehicle_number: str, owner_name: str):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Find first available slot
    cursor.execute(
        "SELECT slot_number FROM parking_slots "
        "WHERE status = 'Available' LIMIT 1"
    )

    slot = cursor.fetchone()

    if slot is None:
        cursor.close()
        connection.close()

        return {
            "message": "No parking slot available"
        }

    slot_number = slot["slot_number"]

    # Change slot status
    cursor.execute(
        "UPDATE parking_slots "
        "SET status = 'Occupied' "
        "WHERE slot_number = %s",
        (slot_number,)
    )

    # Save vehicle details
    cursor.execute(
        """
        INSERT INTO vehicles
        (vehicle_number, owner_name, slot_number, entry_time)
        VALUES (%s, %s, %s, %s)
        """,
        (
            vehicle_number,
            owner_name,
            slot_number,
            datetime.now()
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Vehicle parked successfully",
        "vehicle_number": vehicle_number,
        "owner_name": owner_name,
        "slot_number": slot_number
    }




@app.post("/exit/{vehicle_number}")
def vehicle_exit(vehicle_number: str):

    connection = get_connection()

    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = connection.cursor(dictionary=True)

    # Find the currently parked vehicle
    cursor.execute(
        """
        SELECT *
        FROM vehicles
        WHERE vehicle_number = %s
        AND exit_time IS NULL
        """,
        (vehicle_number,)
    )

    vehicle = cursor.fetchone()

    if not vehicle:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Vehicle not found or already exited"
        )

    # Current exit time
    exit_time = datetime.now()

    # Entry time
    entry_time = vehicle["entry_time"]

    # Calculate parking duration
    duration = exit_time - entry_time

    # Convert seconds to hours
    hours = duration.total_seconds() / 3600

    # Round up partial hour
    parking_hours = math.ceil(hours)

    # Minimum 1 hour
    if parking_hours < 1:
        parking_hours = 1

    # Parking charge
    rate_per_hour = 20

    amount = parking_hours * rate_per_hour

    # Update vehicle record
    cursor.execute(
        """
        UPDATE vehicles
        SET exit_time = %s,
            amount = %s
        WHERE vehicle_id = %s
        """,
        (exit_time, amount, vehicle["vehicle_id"])
    )

    # Make parking slot available again
    cursor.execute(
        """
        UPDATE parking_slots
        SET status = 'Available'
        WHERE slot_number = %s
        """,
        (vehicle["slot_number"],)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Vehicle exited successfully",
        "vehicle_number": vehicle_number,
        "slot_number": vehicle["slot_number"],
        "entry_time": entry_time,
        "exit_time": exit_time,
        "parking_hours": parking_hours,
        "rate_per_hour": rate_per_hour,
        "amount": amount
    }