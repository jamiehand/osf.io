<%inherit file="base.mako"/>
<%def name="title()">Dashboard</%def>
<%def name="content()">
<div mod-meta='{"tpl": "include/subnav.mako", "replace": true}'></div>

<div class="row">
    <div class="col-md-6">
        <div class="page-header">
            <div class="pull-right"><a class="btn btn-default" href="/project/new">New Project</a></div>
            <h3>Projects</h3>
        </div>
        <div mod-meta='{
                 "tpl": "util/render_nodes.mako",
                 "uri": "/api/v1/dashboard/get_nodes/",
                 "replace": true
            }'></div>
    </div>
    <div class="row">
        <div class="col-md-6">
           <div id="watchFeed">
               <div class="page-header">
                    <h3>Watched Projects</h3>
                </div>
                <div id="logScope">
                    <%include file="log_list.mako"/>
                </div><!-- end #logScope -->
            </div><!-- end #watchFeed -->
        </div>
    </div>
</div>

</%def>

<%def name="javascript_bottom()">
<script>
    // Initialize the LogsViewModel
    $script('/static/vendor/bower_components/momentjs/min/moment.min.js', '/static/js/app.js', function() {
        initializeLogs("#logScope", "/api/v1/watched/logs/");
    });
</script>
</%def>
