angular.module('schdl.term', ['ngResource'])

.factory('Term', ['$resource', function($resource) {
  var Term = $resource('/api/terms/:school/:id');
  return Term;
}])

.controller('TermCtrl', ['$scope', '$routeParams', 'Term', 'titleService', 'term', function($scope, $routeParams, Term, titleService, term) {
  $scope.term = term;
  titleService(term.name);
}])

;
