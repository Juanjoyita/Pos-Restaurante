from app import app
from extensions import db
from models import Mesa

with app.app_context():
    for i in range(1, 11):
        mesa = Mesa(numero=i)
        db.session.add(mesa)

    db.session.commit()

print("Mesas creadas correctamente")
