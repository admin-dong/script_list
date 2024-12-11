#jenkins 部署和回归
#！/bin/bash
code_dir="$WORKSPACE"
web_ip=10.0.0.7
tar_code(){
cd $code_dir
tar zcf /opt/web_${git_version}.tar.gz ./*
}

scp_code(){
scp /opt/web_${git_version}.tar.gz $web_ip:/code/
}

tar_xf(){
ssh $web_ip "mkdir /code/web_${git_version}"
ssh $web_ip "cd /code;tar xf web_${git_version}.tar.gz -C web_${git_version};rm -rf web_${git_version}.tar.gz"
}

ln_code(){
ssh $web_ip "cd /code;rm -rf html;ln -s web_${git_version} html"
}

main(){
	tar_code
	scp_code
	tar_xf
	ln_code
}
if [ $deploy_env = "部署" ];then
     if [ "$GIT_COMMIT" = "$GIT_PREVIOUS_SUCCESSFUL_COMMIT" ];then
        echo "当前版本已经部署过不允许重复构建"
        exit
     else
         main
     fi
elif [ $deploy_env = "回滚" ];then
     ln_code
fi