# This script is used to prepare functional test env after devstack
# installation of apmec

DEVSTACK_DIR=${DEVSTACK_DIR:-~/devstack}
APMEC_DIR=$(dirname "$0")/..
PRIVATE_KEY_FILE=${PRIVATE_KEY_FILE:-/dev/null}
MEC_USER=${MEC_USER:-"mec_user"}

# Test devstack dir setting
if [ ! -f ${DEVSTACK_DIR}/openrc ]; then
    echo "Please set right DEVSTACK_DIR"
    exit 1
fi

. $DEVSTACK_DIR/openrc admin admin
. ${APMEC_DIR}/apmec/tests/contrib/post_test_hook_lib.sh

fixup_quota
add_key_if_not_exist
add_secgrp_if_not_exist
