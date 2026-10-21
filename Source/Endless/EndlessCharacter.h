#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "EndlessCharacter.generated.h"

class UCameraComponent;
class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

UCLASS()
class ENDLESS_API AEndlessCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AEndlessCharacter();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Endless")
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Endless")
	float InteractDistance = 200.f;

protected:
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

private:
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void Interact();

	// shortcut: input is built in code (WASD/mouse/E), no rebinding; move to .uasset input when a settings menu is needed.
	UPROPERTY(Transient) TObjectPtr<UInputMappingContext> MappingContext;
	UPROPERTY(Transient) TObjectPtr<UInputAction> MoveAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> LookAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> InteractAction;
};
