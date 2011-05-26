#!/bin/bash
#================
# FILE          : config.sh
#----------------
# PROJECT       : OpenSuSE KIWI Image System
# COPYRIGHT     : (c) 2006 SUSE LINUX Products GmbH. All rights reserved
#               :
# AUTHOR        : Marcus Schaefer <ms@suse.de>
#               :
# BELONGS TO    : Operating System images
#               :
# DESCRIPTION   : configuration script for SUSE based
#               : operating systems
#               :
#               :
# STATUS        : BETA
#----------------
#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

# kiwi doesn't copy /.kconfig from source to build dir
test -f /kconfig && . /kconfig 

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$name]..."

#======================================
# SuSEconfig
#--------------------------------------
echo "** Running suseConfig..."
suseConfig

echo "** Running ldconfig..."
/sbin/ldconfig

#======================================
# Clean up kconfig
#--------------------------------------
echo "** Removing kconfig..."
rm /kconfig



#=====================================
# setting kdm theme to studio
#-------------------------------------
echo '** Setting kdm theme...'
sed -i 's/DISPLAYMANAGER_KDM_THEME=.*/DISPLAYMANAGER_KDM_THEME=studio/g' /etc/sysconfig/displaymanager



#=====================================
# setting gdm theme to 
#-------------------------------------
echo '** Setting gdm background theme...'
gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.vendor --type string -s /desktop/gnome/background/picture_filename '/usr/share/wallpapers/custom_wallpaper.png'

#=====================================
# make the xdm theme a little bit prettier
#-------------------------------------

if [ -e /etc/X11/Xresources ]
then
  echo "xlogin*greeting: Login"                    >> /etc/X11/Xresources
  echo "xlogin*namePrompt: Name: "              >> /etc/X11/Xresources
  echo "xlogin*passwdPrompt: Password: "        >> /etc/X11/Xresources
  echo "xlogin*fail: Failed!"                      >> /etc/X11/Xresources
  echo "xlogin.Login.greetFont: 9x15bold"          >> /etc/X11/Xresources
  echo "xlogin.Login.promptFont: 6x13bold"         >> /etc/X11/Xresources
  echo "xlogin.Login.font: 6x13"                   >> /etc/X11/Xresources
  echo "xlogin.Login.failFont: 6x13"               >> /etc/X11/Xresources
  echo "xlogin*geometry: 300x200"                  >> /etc/X11/Xresources
  echo "xlogin*borderWidth: 1"                     >> /etc/X11/Xresources
  echo "xlogin*frameWidth: 0"                      >> /etc/X11/Xresources
  echo "xlogin*innerFramesWidth: 0"                >> /etc/X11/Xresources
  echo "xlogin*shdColor: black"                    >> /etc/X11/Xresources
  echo "xlogin*hiColor: black"                     >> /etc/X11/Xresources
  echo "xlogin*greetColor: white"                  >> /etc/X11/Xresources
  echo "xlogin*failColor: red"                     >> /etc/X11/Xresources
  echo "xlogin*promptColor: grey75"                >> /etc/X11/Xresources
  echo "xlogin*foreground: grey75"                 >> /etc/X11/Xresources
  echo "xlogin*background: black"                  >> /etc/X11/Xresources
  echo "xlogin*borderColor: grey50 "               >> /etc/X11/Xresources
fi

if [ -e /etc/icewm/preferences ]
then
  sed -i 's#DesktopBackgroundImage=.*#DesktopBackgroundImage="/etc/X11/xdm/BackGround.xpm"#' /etc/icewm/preferences 
fi
if [ -e /etc/X11/xdm/Xsetup ]
then
  sed -i 's#^exit 0$#kill `cat /var/run/xconsole.pid`;/sbin/startproc /usr/bin/icewmbg || /usr/bin/xsetroot -solid lightgray;\nexit 0#g' /etc/X11/xdm/Xsetup 
fi


#======================================
# RPM GPG Keys Configuration
#--------------------------------------
echo '** Importing GPG Keys...'
rpm --import /studio/studio_rpm_key_0
#rm /studio/studio_rpm_key_0
rpm --import /studio/studio_rpm_key_1
#rm /studio/studio_rpm_key_1
rpm --import /studio/studio_rpm_key_2
#rm /studio/studio_rpm_key_2
rpm --import /studio/studio_rpm_key_3
#rm /studio/studio_rpm_key_3
rpm --import /studio/studio_rpm_key_4
#rm /studio/studio_rpm_key_4
rpm --import /studio/studio_rpm_key_5
#rm /studio/studio_rpm_key_5
rpm --import /studio/studio_rpm_key_6
#rm /studio/studio_rpm_key_6
rpm --import /studio/studio_rpm_key_7
#rm /studio/studio_rpm_key_7
rpm --import /studio/studio_rpm_key_8
#rm /studio/studio_rpm_key_8

sed --in-place -e 's/icewm/icewm-session/' /usr/bin/wmlist

sed --in-place -e 's/# solver.onlyRequires.*/solver.onlyRequires = true/' /etc/zypp/zypp.conf

# Enable sshd
chkconfig sshd on
chown root:root /build-custom
chmod +x /build-custom
# run custom build_script after build
/build-custom
chown root:root /etc/init.d/suse_studio_custom
chmod +x /etc/init.d/suse_studio_custom
test -d /studio || mkdir /studio
cp /image/.profile /studio/profile
cp /image/config.xml /studio/config.xml
true