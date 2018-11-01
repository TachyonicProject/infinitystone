
function reset_role(e) {
    $('#role_add').val(null).trigger('change');
    domain = $('#role_add_domain').val();
    tenant_id = $('#role_add_tenant_id').val();
    $('#role_add').attr('data-url','/v1/access/' + domain + '/' + tenant_id);
}
function reset_tenant(e) {
    $('#role_add_tenant_id').val(null).trigger('change');
    domain = $('#role_add_domain').val()
    if (domain == '') {
        domain = 'None'
    }
    $('#role_add_tenant_id').attr('data-url','/v1/tenants/' + domain)
    reset_role(e);
}
