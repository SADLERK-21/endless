#include "EndlessCharacter.h"
#include "Endless.h"
#include "Interactable.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SpotLightComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"

AEndlessCharacter::AEndlessCharacter()
{
	GetCapsuleComponent()->InitCapsuleSize(40.f, 90.f);
	GetCharacterMovement()->MaxWalkSpeed = 180.f; // slow walk: the player must have time to look

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(GetCapsuleComponent());
	Camera->SetRelativeLocation(FVector(0.f, 0.f, 64.f));
	Camera->bUsePawnControlRotation = true;

	Flashlight = CreateDefaultSubobject<USpotLightComponent>(TEXT("Flashlight"));
	Flashlight->SetupAttachment(Camera);
	Flashlight->SetRelativeLocation(FVector(10.f, 15.f, -10.f));
	Flashlight->SetInnerConeAngle(12.f);
	Flashlight->SetOuterConeAngle(28.f);
	Flashlight->SetAttenuationRadius(1500.f);
	Flashlight->SetVisibility(false);
}

void AEndlessCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	auto MakeAction = [this](EInputActionValueType Type)
	{
		UInputAction* Action = NewObject<UInputAction>(this);
		Action->ValueType = Type;
		return Action;
	};
	MoveAction = MakeAction(EInputActionValueType::Axis2D);
	LookAction = MakeAction(EInputActionValueType::Axis2D);
	InteractAction = MakeAction(EInputActionValueType::Boolean);
	FlashlightAction = MakeAction(EInputActionValueType::Boolean);

	MappingContext = NewObject<UInputMappingContext>(this);
	// D = +X, A = -X, W = +Y (swizzle), S = -Y (swizzle + negate)
	MappingContext->MapKey(MoveAction, EKeys::D);
	MappingContext->MapKey(MoveAction, EKeys::A).Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));
	MappingContext->MapKey(MoveAction, EKeys::W).Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(MappingContext));
	FEnhancedActionKeyMapping& Back = MappingContext->MapKey(MoveAction, EKeys::S);
	Back.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(MappingContext));
	Back.Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));

	UInputModifierNegate* InvertY = NewObject<UInputModifierNegate>(MappingContext);
	InvertY->bX = false;
	InvertY->bZ = false;
	MappingContext->MapKey(LookAction, EKeys::Mouse2D).Modifiers.Add(InvertY);

	MappingContext->MapKey(InteractAction, EKeys::E);
	MappingContext->MapKey(FlashlightAction, EKeys::F);

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			Subsystem->AddMappingContext(MappingContext, 0);
		}
	}

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!Input)
	{
		UE_LOG(LogEndless, Error, TEXT("EnhancedInputComponent missing - check Config/DefaultInput.ini"));
		return;
	}
	Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AEndlessCharacter::Move);
	Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &AEndlessCharacter::Look);
	Input->BindAction(InteractAction, ETriggerEvent::Started, this, &AEndlessCharacter::Interact);
	Input->BindAction(FlashlightAction, ETriggerEvent::Started, this, &AEndlessCharacter::ToggleFlashlight);
}

void AEndlessCharacter::Move(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddMovementInput(GetActorForwardVector(), Axis.Y);
	AddMovementInput(GetActorRightVector(), Axis.X);
}

void AEndlessCharacter::Look(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddControllerYawInput(Axis.X);
	AddControllerPitchInput(Axis.Y);
}

void AEndlessCharacter::Interact()
{
	const FVector Start = Camera->GetComponentLocation();
	const FVector End = Start + Camera->GetForwardVector() * InteractDistance;
	FHitResult Hit;
	const FCollisionQueryParams Params(SCENE_QUERY_STAT(EndlessInteract), false, this);
	if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
	{
		AActor* Target = Hit.GetActor();
		if (Target && Target->Implements<UInteractable>())
		{
			IInteractable::Execute_Interact(Target, this);
		}
	}
}

void AEndlessCharacter::ToggleFlashlight()
{
	Flashlight->ToggleVisibility();
	OnFlashlightToggled(Flashlight->IsVisible());
}
