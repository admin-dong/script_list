for i in `seq 2 2 254`
do
        ping  -c 1 -w 1 203.107.6.$i &>/dev/null && echo "203.107.6.$i  ok" || echo "203.107.6.$i       ng"
done

exit

#or 
for ((i=1; i<=254; i++))
do
        if [ $(($i%2)) -eq 0 ]
        then
                ping  -c 1 -w 1 203.107.6.$i 2>&1 >/dev/null
                if [ $? -eq 0 ]
                then
                        echo "203.107.6.$i       OK"
                fi
        fi
done
