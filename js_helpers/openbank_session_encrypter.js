// https://api-ob.nd.nudatasecurity.com/2.2/w/w-766580/sync/js/
// found by var nsqpbp,nspdppdddp="NDSASESS",nspqqqb="3600",nsdbpd="ndsi"+ndjsStaticVersion,nspdp="ndsid"
// where nspdp="ndsid" points to <input name="ndsid" type="hidden" value="ndsa40ekvea1luvjnw9ikas">
function encrypt (){var a=new Date;return"ndsa"+Math.random().toString(36).substr(2,16)+a.getTime().toString(36)}

(function () {
  console.log(encrypt());
})();