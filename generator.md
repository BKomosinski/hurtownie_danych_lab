Generator tworzy plik csv z symulowanymi danymi o ruchu pojazdów
Odpala się komendą

`python generator.py`


 Szybki start (dane historyczne kampusu Piotrowo, 10Hz, 8 minut):
python generator.py

 Uruchomienie z własnymi parametrami:
`python generator.py -o trasa.csv -d 120 -f 5 --lat 52.40 --lon 16.95`

  Dostępne parametry (flagi)
```
 -o / --output       Nazwa pliku wyjściowego 
 -d / --duration     Czas trwania symulacji w sekundach 
 -f / --frequency    Częstotliwość próbek w Hz 
 -n / --num-rovers   Ilość pojazdów
 -s / --sensors     Liczba statycznych czujników na polu 
 ```