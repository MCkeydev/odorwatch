import mqtt from 'mqtt';
import firebase from 'firebase-admin';
import { readFile } from 'fs/promises';

// --- 🔐 Configuration MQTT ---
const MQTT_HOST = 'mqtt://mosquitto';
const MQTT_USERNAME = 'user1';
const MQTT_PASSWORD = '123456789';

// --- 🔥 Initialisation Firebase ---
const serviceAccount = JSON.parse(
  await readFile(new URL('./firebase-service-account.json', import.meta.url), 'utf-8')
);

firebase.initializeApp({
  credential: firebase.credential.cert(serviceAccount),
  databaseURL: 'https://odorwatch.firebaseio.com',
});

const db = firebase.firestore();

// --- 📦 Fonction pour mettre à jour une toilette via son ESP ID ---
async function updateToiletByEspId(espId, updateData) {
  try {
    const querySnapshot = await db.collection('toilets').where('esp_id', '==', espId).get();

    if (querySnapshot.empty) {
      console.log(`❌ Aucun document trouvé avec esp_id: ${espId}`);
      return;
    }

    for (const doc of querySnapshot.docs) {
      await db.collection('toilets').doc(doc.id).update(updateData);
      console.log(`✅ Document avec esp_id "${espId}" mis à jour.`);
    }
  } catch (error) {
    console.error('❌ Erreur lors de la mise à jour du document :', error);
  }
}

// --- 🌐 Connexion au broker MQTT ---
const client = mqtt.connect(MQTT_HOST, {
  username: MQTT_USERNAME,
  password: MQTT_PASSWORD,
});

client.on('connect', () => {
  console.log('✅ Connecté au broker MQTT');
  client.subscribe('odorwatch/gassensor', (err) => {
    if (err) console.error('❌ Erreur de souscription :', err);
    else console.log('📡 Abonné au topic "odorwatch/gassensor"');
  });
});

client.on('message', async (topic, message) => {
  if (topic === 'odorwatch/gassensor') {
    try {
      const data = JSON.parse(message.toString());

      console.log('📤 Données envoyées à Firebase :', data);
      if (data.esp_id && data.available !== undefined) {
        const timestampArray = data.timestamp;
        const jsDate = new Date(Date.UTC(
          timestampArray[0],          // Year
          timestampArray[1] - 1,      // Month (0-indexed)
          timestampArray[2],          // Day
          timestampArray[3],          // Hour
          timestampArray[4],          // Minute
          timestampArray[5],          // Second
          timestampArray[6]           // Millisecond
        ));
        await updateToiletByEspId(data.esp_id, {
          ...data,
          timestamp: jsDate,
        });
      }
    } catch (error) {
      console.error('❌ Erreur lors du traitement du message :', error);
    }
  }
});

client.on('error', (error) => {
  console.error('❌ Erreur MQTT :', error);
});
