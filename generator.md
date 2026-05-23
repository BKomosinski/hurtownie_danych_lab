Generator tworzy plik csv z symulowanymi danymi o ruchu pojazdów
Odpala się komendą

`python generator.py`


 Szybki start (dane historyczne kampusu Piotrowo, 10Hz, 8 minut):
python generator.py

 Uruchomienie z własnymi parametrami:
`python generator.py -o trasa.csv -d 120 -f 5 --lat 52.40 --lon 16.95`

  Dostępne parametry (flagi)
```
 -o / --output       Nazwa pliku wyjściowego (np. moje_dane.csv)    
 -d / --duration     Czas trwania symulacji w sekundach (np. 120)  
 -f / --frequency    Częstotliwość próbek w Hz (np. 5)
 --lat               Początkowa szerokość geograficzna (np. 52.40)
 --lon               Początkowa długość geograficzna (np. 16.95)
 --alt               Początkowa wysokość n.p.m. (np. 100.0)
 --start-time        Czas początkowy w nanosekundach UNIX Epoch
 ```