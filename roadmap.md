AC replace floor ceiling 

[ESP32/ESP8266 device] <--MQTT--> [MQTT Broker] <--MQTT--> [FastAPI backend]
                                                                    |
                                                              WebSocket
                                                                    |
                                                                    v
                                                          [React frontend]

                    Sensors/Relays
                          │
                          ▼
                 ESP32 / ESP8266
                          │
                  MQTT Publish/Subscribe
                          │
                          ▼
                    MQTT Broker
                  (Mosquitto/EMQX)
                          │
          ┌───────────────┴────────────────┐
          │                                │
          ▼                                ▼
  FastAPI Backend                  Other Smart Devices
          │
          ├── PostgreSQL Database
          │
          ├── Authentication (JWT)
          │
          ├── Automation Rules
          │
          ├── Device Management
          │
          ├── REST API
          │
          └── WebSocket Server
                    │
                    ▼
          React Web Dashboard
                    │
                    ▼
            User Controls Devices

                +-------------------------+
                |      React Frontend     |
                +------------▲------------+
                             │ WebSocket
                             │
                +------------┴------------+
                |       FastAPI API       |
                |-------------------------|
                | REST API                |
                | Authentication          |
                | Automation Engine       |
                | MQTT Client             |
                +------------▲------------+
                             │
                  MQTT Publish/Subscribe
                             │
                +------------┴------------+
                |       MQTT Broker       |
                |   (Mosquitto / EMQX)    |
                +------------▲------------+
                             │
        +--------------------+--------------------+
        │                    │                    │
     ESP32 #1            ESP32 #2            ESP32 #3
 (Living Room)        (Kitchen)          (Bedroom)
        │                    │                    │
   Sensors/Relays      Sensors/Relays      Sensors/Relays

                +-------------------------+
                |      PostgreSQL         |
                | Users                   |
                | Devices                 |
                | Sensor Logs             |
                | Automation Rules        |
                | Notifications           |
                +-------------------------+

add the aeroplane in the home hero section between the premium section and the airline support section, add an admin access to enable the uploading of destination, destination detail and Popular offers,