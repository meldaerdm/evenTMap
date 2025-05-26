from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, requests

app = Flask(__name__)
app.secret_key = 'secret'

def veritabani_baglantisi():
    conn = sqlite3.connect('veritabani.db')
    return conn

@app.route('/ana_ekran')
def ana_ekran():
    return render_template("ana_ekran.html")


@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        hashed_pw = generate_password_hash(password)

        conn = veritabani_baglantisi()
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email=?", (email,))
        if c.fetchone():
            flash("Bu e-posta zaten kayıtlı!")
            conn.close()
            return redirect(url_for('kayit'))
        
        c.execute("""
            INSERT INTO users (email, password, is_approved, first_login) VALUES (?,?,?,?)
          """,(email,hashed_pw,False,1))
        
        conn.commit()
        conn.close()

        flash("Kayıt Başarılı Yönetici Onayı Bekleniyor.")
        return redirect(url_for('kayit'))
    
    return render_template('kayit.html')


@app.route('/onay')
def onay_bekleyenler():
    conn = veritabani_baglantisi()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE is_approved=0")
    users = c.fetchall()

    conn.close()

    return render_template('onay_bekleyenler.html', users=users)

@app.route('/onayla/<int:user_id>', methods=['POST'])
def onayla(user_id):
    conn = veritabani_baglantisi()
    c = conn.cursor()

    c.execute("UPDATE users SET is_approved=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    flash("Kullanıcı Onaylandı")
    return redirect(url_for('onay_bekleyenler'))

@app.route('/giris', methods=['GET','POST'])
def giris():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = veritabani_baglantisi()
        c = conn.cursor()

        c.execute("SELECT id, password, is_approved, first_login FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user:
            user_id, hashed_pw, is_approved, first_login = user

            if not is_approved:
                flash("yönetici onayı bekleniyor.")
                return redirect(url_for('giris'))
            
            if check_password_hash(hashed_pw, password):
                session['user_id']=user_id

                if int(first_login) == 1:
                    return redirect(url_for('sifre_degistir'))
                
                flash("Giriş Başarılı!")
                return redirect(url_for('ana_ekran'))
            else:
                flash("ŞİFRE YANLIŞ!")

        else:
            flash("kullanıcı bulunamadı.")

    return render_template('giris.html')
            
@app.route('/sifre_degistir', methods=['GET', 'POST'])
def sifre_degistir():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        user_id = session.get('user_id')

        conn = veritabani_baglantisi()
        c = conn.cursor()

        # Mevcut şifreyi al
        c.execute("SELECT password FROM users WHERE id=?", (user_id,))
        result = c.fetchone()

        if result and check_password_hash(result[0], old_password):
            # Eski şifre doğruysa güncelle
            hashed_new = generate_password_hash(new_password)
            c.execute("UPDATE users SET password=?, first_login=0 WHERE id=?", (hashed_new, user_id))
            conn.commit()
            conn.close()
            flash("Yeni şifre başarıyla değiştirildi.")
            return redirect(url_for('ana_ekran'))
        else:
            conn.close()
            flash("Eski şifre hatalı!")
            return redirect(url_for('sifre_degistir'))

    return render_template('sifre_degistir.html')


TURKIYE_SEHIRLERI = [
    "Istanbul", "Ankara", "Izmir", "Bursa", "Adana", "Antalya", "Konya", "Gaziantep", "Kayseri", "Eskişehir"
]

API_KEY = "F1EYIvZ8FXmKGA3G3PjCD5Sp40zovMoi"

@app.route('/konserler')
def konserler():
    sehir = request.args.get("sehir", default="Istanbul")
    tarih = request.args.get("tarih")

    params = {
        "apikey": API_KEY,
        "countryCode": "TR",
        "classificationName": "music",
        "size": 20,
        "sort": "date,asc"
    }

    if sehir:
        params["city"] = sehir

    try:
        response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
        data = response.json()

        etkinlikler = []
        if "_embedded" in data:
            for event in data["_embedded"]["events"]:
                # FOTOĞRAF SEÇİMİ (en büyük olan)
                foto_url = "/static/default.jpg"
                if "images" in event and event["images"]:
                    sorted_images = sorted(event["images"], key=lambda x: x.get("width", 0), reverse=True)
                    for img in sorted_images:
                        if img.get("url") and img.get("width", 0) >= 600:
                            foto_url = img["url"]
                            break                

                etkinlikler.append({
                    "isim": event["name"],
                    "tarih": event["dates"]["start"].get("localDate", "Yok"),
                    "saat": event["dates"]["start"].get("localTime", "Yok"),
                    "foto": foto_url,
                    "mekan": event["_embedded"]["venues"][0]["name"],
                    "fiyat": etkinlik_fiyati(event["name"])
                })
        else:
            etkinlikler = []

    except Exception as e:
        print("API hatası:", e)
        etkinlikler = []

    return render_template(
        "konserler.html",
        etkinlikler=etkinlikler,
        sehirler=TURKIYE_SEHIRLERI,
        secili_sehir=sehir,
        secili_tarih=tarih
    )

@app.route('/festivaller')
def festivaller():
    sehir = request.args.get("sehir", default="Istanbul")
    tarih = request.args.get("tarih")

    params = {
        "apikey": API_KEY,
        "countryCode": "TR",
        "size": 100,
        "sort": "date,asc",
        "keyword": "festival"
    }

    if sehir:
        params["city"] = sehir

    try:
        response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
        data = response.json()

        etkinlikler = []
        if "_embedded" in data:
            for event in data["_embedded"]["events"]:
                foto_url = "/static/default2.jpg"
                if "images" in event and event["images"]:
                    sorted_images = sorted(event["images"], key=lambda x: x.get("width", 0), reverse=True)
                    for img in sorted_images:
                        if img.get("url") and img.get("width", 0) >= 600:
                            foto_url = img["url"]
                            break

                etkinlikler.append({
                    "isim": event["name"],
                    "tarih": event["dates"]["start"].get("localDate", "Yok"),
                    "saat": event["dates"]["start"].get("localTime", "Yok"),
                    "foto": foto_url,
                    "mekan": event["_embedded"]["venues"][0]["name"],
                    "fiyat": etkinlik_fiyati(event["name"])
                })
        else:
            etkinlikler = []

    except Exception as e:
        print("Festival API hatası:", e)
        etkinlikler = []

    return render_template(
        "festivaller.html",
        etkinlikler=etkinlikler,
        sehirler=TURKIYE_SEHIRLERI,
        secili_sehir=sehir,
        secili_tarih=tarih
    )

@app.route('/partiler')
def partiler():
    sehir = request.args.get("sehir", default="Istanbul")
    tarih = request.args.get("tarih")

    params = {
        "apikey": API_KEY,
        "countryCode": "TR",
        "size": 20,
        "sort": "date,asc",
        "keyword": "party"  # festival gibi keyword ile daha iyi sonuç verir
    }

    if sehir:
        params["city"] = sehir

    try:
        response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
        data = response.json()

        etkinlikler = []
        if "_embedded" in data:
            for event in data["_embedded"]["events"]:
                foto_url = "/static/default3.jpg"
                if "images" in event and event["images"]:
                    sorted_images = sorted(event["images"], key=lambda x: x.get("width", 0), reverse=True)
                    for img in sorted_images:
                        if img.get("url") and img.get("width", 0) >= 600:
                            foto_url = img["url"]
                            break

                print("Etkinlik:", event["name"])
                print("Foto URL:", foto_url)
                


                etkinlikler.append({
                    "isim": event["name"],
                    "tarih": event["dates"]["start"].get("localDate", "Yok"),
                    "saat": event["dates"]["start"].get("localTime", "Yok"),
                    "foto": foto_url,
                    "mekan": event["_embedded"]["venues"][0]["name"],
                    "fiyat": etkinlik_fiyati(event["name"])
                })
        else:
            etkinlikler = []

    except Exception as e:
        print("Parti API hatası:", e)
        etkinlikler = []

    return render_template(
        "partiler.html",
        etkinlikler=etkinlikler,
        sehirler=TURKIYE_SEHIRLERI,
        secili_sehir=sehir,
        secili_tarih=tarih
    )

@app.route('/dj')
def dj():
    sehir = request.args.get("sehir", default="Istanbul")
    tarih = request.args.get("tarih")

    params = {
        "apikey": API_KEY,
        "countryCode": "TR",
        "size": 20,
        "sort": "date,asc",
        "keyword": "DJ"
    }

    if sehir:
        params["city"] = sehir

    try:
        response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
        data = response.json()

        etkinlikler = []
        if "_embedded" in data:
            for event in data["_embedded"]["events"]:
                foto_url = "/static/default.jpg"
                if "images" in event and event["images"]:
                    sorted_images = sorted(event["images"], key=lambda x: x.get("width", 0), reverse=True)
                    for img in sorted_images:
                        if img.get("url") and img.get("width", 0) >= 600:
                            foto_url = img["url"]
                            break

                etkinlikler.append({
                    "isim": event["name"],
                    "tarih": event["dates"]["start"].get("localDate", "Yok"),
                    "saat": event["dates"]["start"].get("localTime", "Yok"),
                    "foto": foto_url,
                    "mekan": event["_embedded"]["venues"][0]["name"],
                    "fiyat": etkinlik_fiyati(event["name"])
                })
        else:
            etkinlikler = []

    except Exception as e:
        print("DJ API hatası:", e)
        etkinlikler = []

    return render_template(
        "dj.html",
        etkinlikler=etkinlikler,
        sehirler=TURKIYE_SEHIRLERI,
        secili_sehir=sehir,
        secili_tarih=tarih
    )


@app.route('/sepete_ekle', methods=['POST'])
def sepete_ekle():
    etkinlik = {
        "isim": request.form['isim'],
        "tarih": request.form['tarih'],
        "saat": request.form['saat'],
        "mekan": request.form['mekan'],
        "foto": request.form['foto'],
        "fiyat": etkinlik_fiyati(request.form['isim'])  # fiyatı ekledik
    }

    if 'sepet' not in session:
        session['sepet'] = []

    session['sepet'].append(etkinlik)
    session.modified = True
    return redirect(request.referrer)


def etkinlik_fiyati(isim):
    isim = isim.lower()
    if "festival" in isim:
        return 1000
    elif "rock" in isim:
        return 750
    elif "pop" in isim:
        return 500
    elif "rap" in isim:
        return 600
    elif "dj" in isim:
        return 400
    elif "parti" in isim or "party" in isim:
        return 350
    return 500  # default fiyat



@app.route('/sepet')
def sepet():
    sepet = session.get('sepet', [])
    toplam = sum(item['fiyat'] for item in sepet)
    return render_template('sepet.html', sepet=sepet, toplam=toplam)


@app.route("/sepetten_sil/<int:index>", methods=["POST"])
def sepetten_sil(index):
    if "sepet" in session:
        try:
            session["sepet"].pop(index)
            session.modified = True
        except IndexError:
            pass
    return redirect(url_for("sepet"))


@app.route('/odeme')
def odeme():
    return render_template('odeme.html')



if __name__ == '__main__':
    app.run(debug=True)

