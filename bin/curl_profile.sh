curl -X GET http://localhost:8080/__profile__

curl -X POST -o proxy.profile --data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=binary&download=Download' http://localhost:8080/__profile__
curl -X POST -o profile1234.json --data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=json&download=Download' http://localhost:8080/__profile__
curl -X POST -o profile1234.csv --data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=csv&download=Download' http://localhost:8080/__profile__
curl -X POST -o profile1234.ods --data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=odf&download=Download' http://localhost:8080/__profile__

wget http://localhost:8080/__profile__
wget -O proxy.profile --post-data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=binary&download=Download' http://localhost:8080/__profile__
wget -O profile1234.json --post-data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=json&download=Download' http://localhost:8080/__profile__
wget -O profile1234.csv --post-data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=csv&download=Download' http://localhost:8080/__profile__
wget -O profile1234.ods --post-data 'profile=current&sort=time&limit=-1&mode=stats&filename=&metric=nc&plottype=bar&format=odf&download=Download' http://localhost:8080/__profile__