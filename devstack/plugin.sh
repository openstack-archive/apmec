# plugin.sh - Devstack extras script to install apmec

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

echo_summary "apmec's plugin.sh was called..."
. $DEST/apmec/devstack/lib/apmec
(set -o posix; set)

# check for service enabled
if is_service_enabled apmec; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        echo_summary "Installing Apmec"
        install_apmec
        echo_summary "Installing tosca parser"
        mec_tosca_parser_install
        echo_summary "Installing heat translator"
        mec_heat_translator_install

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        # Configure after the other layer 1 and 2 services have been configured
        echo_summary "Configuring Apmec"
        configure_apmec
        create_apmec_accounts

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Installing apmec horizon"
        apmec_horizon_install
        # Initialize and start the apmec service
        echo_summary "Initializing Apmec"
        init_apmec
        echo_summary "Starting Apmec API and conductor"
        start_apmec
        echo_summary "Installing apmec client"
        apmec_client_install
        if [[ "${APMEC_MODE}" == "all" ]]; then
            echo_summary "Modifying Heat policy.json file"
            modify_heat_flavor_policy_rule
            echo_summary "Setup initial apmec network"
            apmec_create_initial_network
            echo_summary "Check and download images for apmec initial"
            apmec_check_and_download_images
            echo_summary "Registering default VIM"
            apmec_register_default_vim
        fi
    fi

    if [[ "$1" == "unstack" ]]; then
        # Shut down apmec services
	stop_apmec
    fi

    if [[ "$1" == "clean" ]]; then
        # Remove state and transient data
        # Remember clean.sh first calls unstack.sh
        cleanup_apmec
    fi
fi

# Restore xtrace
$XTRACE

# Tell emacs to use shell-script-mode
## Local variables:
## mode: shell-script
## End:

