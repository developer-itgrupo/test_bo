openerp.calquipa_reportemexicanos_parte1_it = function (instance) {
    instance.web.list.columns.add('field.mywidget', 'instance.calquipa_reportemexicanos_parte1_it.mywidget');
    instance.calquipa_reportemexicanos_parte1_it.mywidget = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            res = this._super.apply(this, arguments);

            var amount = parseFloat(res);
            console.log("validando," + amount)
            if (amount < 0){
                var amount = -parseFloat(res);
                var n = amount.toFixed(2)
                return "<font color='#ff0000'>("+(n)+")</font>";
            }
            else{
                var n = amount.toFixed(2)
                return n;

            }
            return res
        }
    });



    instance.web.list.columns.add('field.report_title_color', 'instance.calquipa_reportemexicanos_parte1_it.report_title_color');
    instance.calquipa_reportemexicanos_parte1_it.report_title_color = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            
            res = this._super.apply(this, arguments);

            var title = res;
            if (title == "CIRCULANTE" || title == "Total Disponible" || title == "Total Exigible" || title == "Total Realizable" || title == "Total Circulante" || title == "FIJO" || title == "Total Activo Fijo" || title == "Total Fijo" || title == "DIFERIDO" || title == "Suma del Activo" || title == "Suma del Pasivo" || title == "CAPITAL CONTABLE" || title == "Total Capital Contable" || title == "Suma del Pasivo y Capital" || title == "CIRCULANTE" || title == "CIRCULANTE"){
                return "<b><font color='#0000ff'>"+(title)+"</font></b>";

            }
            else{
                return title;

            }
            return res
        }
    });




    instance.web.list.columns.add('field.report_title_color_resaltado', 'instance.calquipa_reportemexicanos_parte1_it.report_title_color_resaltado');
    instance.calquipa_reportemexicanos_parte1_it.report_title_color_resaltado = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            console.log(row_data);
            console.log(options);
            
            res = this._super.apply(this, arguments);

            var title = res;
            if (row_data.resaltado.value == true){
                return "<b><font color='#0000ff'>"+(title)+"</font></b>";

            }
            else{
                return title;

            }
            return res
        }
    });


    //
    //here you can add more widgets if you need, as above...
    //
};