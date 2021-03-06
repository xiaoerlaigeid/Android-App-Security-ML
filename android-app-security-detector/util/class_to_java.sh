#! /bin/bash
jad=/home/wtq/develop/developtools/jad-tools/jad
function read_dir(){
    workdir=$1
    cd ${workdir}
    for file in `ls $1`
    do
        if [ -d $1"/"$file ]; then
            cd ${file}

            read_dir $1"/"$file
            cd ..
        else
            name=${file#*.} 
            if [ $name = class ]; then
             # timeout的作用是延迟4s kill C,  123457vjad，防止jad反编译时阻塞程序卡住
             timeout 5 $jad -sjava $1"/"$file
            fi
            rm $1"/"$file
        fi
    done
}

read_dir $1
echo "end!!"
