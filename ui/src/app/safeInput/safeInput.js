angular.module('schdl.safeInput', [])

.directive('safeInput', function() {
  return {
    restrict: 'A',
    scope: {
      safeInput: '='
    },
    controller: ['$scope', '$element', function($scope, $element) {
      $scope.safeInput = function() {
        return $element.val();
      };
    }]
  };
})

;
