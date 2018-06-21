angular.module('schdl.school', ['ngResource'])

.controller('SchoolCtrl', ['school', 'titleService', function(school, titleService) {
  titleService(school.name + ' Course Listings');
}])

.factory('School', ['$rootScope', '$location', '$resource', function($rootScope, $location, $resource) {
  var SchoolResource = $resource('/api/schools/host::host');
  var host = $location.search().force_host || $location.host();
  var school = SchoolResource.get({host: host}, function() {
    var lookup = {};
    for (var i = 0; i < school.requirements.length; i++) {
      var req = school.requirements[i];
      lookup[req.id] = req;
    }
    school.getRequirements = function(reqs) {
      var result = [];
      for (var i = 0; i < reqs.length; i++) {
        result.push(lookup[reqs[i]]);
      }
      return result;
    };
  });
  $rootScope.school = school;
  return school;
}])

;
