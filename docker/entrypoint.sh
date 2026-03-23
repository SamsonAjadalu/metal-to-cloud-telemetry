#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/humble/setup.bash
source /ros_ws/install/setup.bash

export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"

# Optional: Gazebo GUI (gzclient) in a browser via noVNC + TigerVNC virtual display :1
if [[ "${USE_WEB_GUI:-0}" == "1" ]]; then
  export DISPLAY=:1
  export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
  export GALLIUM_DRIVER="${GALLIUM_DRIVER:-llvmpipe}"
  export QT_X11_NO_MITSHM="${QT_X11_NO_MITSHM:-1}"

  mkdir -p "${HOME}/.vnc"
  VNC_PASSWORD="${VNC_PASSWORD:-rosdocker}"
  printf '%s\n' "${VNC_PASSWORD}" | vncpasswd -f >"${HOME}/.vnc/passwd"
  chmod 600 "${HOME}/.vnc/passwd"

  cat >"${HOME}/.vnc/xstartup" <<'XS'
#!/bin/sh
openbox-session &
XS
  chmod +x "${HOME}/.vnc/xstartup"

  vncserver :1 -geometry "${VNC_GEOMETRY:-1280x800}" -depth 24 -localhost no -SecurityTypes VncAuth

  NOVNC_PORT="${NOVNC_PORT:-6080}"
  if [[ -x /usr/share/novnc/utils/novnc_proxy ]]; then
    /usr/share/novnc/utils/novnc_proxy --vnc localhost:5901 --listen "${NOVNC_PORT}" &
  elif [[ -x /usr/bin/websockify ]]; then
    websockify --web=/usr/share/novnc "${NOVNC_PORT}" localhost:5901 &
  else
    echo "[docker-entrypoint] WARN: noVNC helper not found; open http://VPS:6080 manually if installed." >&2
  fi
  sleep 2
  echo "[docker-entrypoint] Open in browser: http://<host>:${NOVNC_PORT}  (set VNC_PASSWORD env; default rosdocker)"
fi

if [[ "$#" -eq 0 ]]; then
  RV="${USE_RVIZ:-false}"
  if [[ "${USE_WEB_GUI:-0}" == "1" ]]; then
    HL="false"
  else
    HL="${HEADLESS:-true}"
  fi
  exec ros2 launch robot_bridge stack_sim_nav2.launch.py "headless:=${HL}" "use_rviz:=${RV}"
else
  exec "$@"
fi
